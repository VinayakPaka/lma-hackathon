"""
GreenGuard ESG Platform - File Service
Encapsulates file upload and background processing logic.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.document import Document
from app.services.pdf_service import pdf_service
from app.services.ocr_service import ocr_service
from app.services.embedding_service import embedding_service
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def extract_text_background(document_id: int, file_path: str, file_type: str):
    """Background task to extract text and generate embeddings."""
    logger.info(f"Starting background text extraction for document {document_id}")
    
    db = None
    try:
        db = AsyncSessionLocal()
        
        # 1. Extract Text
        text = ""
        if file_type == "pdf":
            text = pdf_service.extract_text(file_path)
        else:
            text = ocr_service.extract_text(file_path)
            
        doc_result = await db.execute(select(Document).where(Document.id == document_id))
        doc = doc_result.scalar_one_or_none()
        
        if doc:
            doc.extracted_text = text or ""
            doc.extraction_status = "completed" if text else "failed"
            await db.commit()
            
            # 2. Generate Embeddings
            if text and len(text.strip()) > 0:
                # Assuming embedding_service handles checks internally or we do it here
                if settings.VOYAGE_API_KEY and settings.SUPABASE_URL:
                    try:
                        chunks = embedding_service.chunk_text(text)
                        if chunks:
                            chunk_texts = [c["text"] for c in chunks]
                            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
                            embedding_service.store_embeddings(document_id, chunks, embeddings)
                            logger.info(f"Generated and stored embeddings for document {document_id}")
                    except Exception as e:
                        logger.error(f"Embedding failed for doc {document_id}: {e}")
            
    except Exception as e:
        logger.error(f"Background processing failed for doc {document_id}: {e}")
        if db:
            await db.rollback() # Try rollback if session active
    finally:
        if db:
            await db.close()

class FileService:
    
    async def save_upload_file(self, file: UploadFile, user_id: int, db: AsyncSession) -> Document:
        """Save uploaded file to disk and create DB record."""
        ext = Path(file.filename).suffix.lower().lstrip(".")
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")
        
        file_type = "pdf" if ext == "pdf" else "image"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
        
        # Ensure upload dir exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
             raise HTTPException(status_code=400, detail="File too large")
             
        with open(file_path, "wb") as f:
            f.write(content)
            
        document = Document(
            user_id=user_id,
            file_path=file_path,
            file_name=file.filename,
            file_type=file_type,
            file_size=len(content),
            extraction_status="processing"
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document

    def trigger_processing(self, background_tasks: BackgroundTasks, document_id: int, file_path: str, file_type: str):
        """Trigger background processing (extraction + embedding)."""
        background_tasks.add_task(extract_text_background, document_id, file_path, file_type)

file_service = FileService()

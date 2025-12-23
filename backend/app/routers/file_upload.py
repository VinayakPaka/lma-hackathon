"""
GreenGuard ESG Platform - File Upload Router
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.upload_schema import DocumentUploadResponse, DocumentResponse
from app.config import settings
from app.services.pdf_service import pdf_service
from app.services.ocr_service import ocr_service
from app.utils.jwt_handler import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


async def extract_text_background(document_id: int, file_path: str, file_type: str):
    """Background task to extract text from uploaded document and generate embeddings."""
    from app.database import AsyncSessionLocal
    from app.services.embedding_service import embedding_service
    from app.config import settings
    import traceback
    
    logger.info(f"Starting background text extraction for document {document_id}")
    
    # Use a separate session for the background task with proper cleanup
    db = None
    try:
        db = AsyncSessionLocal()
        
        # Step 1: Extract text
        logger.info(f"Extracting text from {file_type} file: {file_path}")
        if file_type == "pdf":
            text = pdf_service.extract_text(file_path)
        else:
            text = ocr_service.extract_text(file_path)
        
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.extracted_text = text or ""
            doc.extraction_status = "completed" if text else "failed"
            await db.commit()
            logger.info(f"Text extraction completed for document {document_id}, text length: {len(text) if text else 0}")
            
            # Step 2: Generate embeddings if text extraction succeeded
            if text and len(text.strip()) > 0:
                # Check if Voyage API is configured
                if not settings.VOYAGE_API_KEY:
                    logger.warning(f"VOYAGE_API_KEY not configured, skipping embedding generation for document {document_id}")
                elif not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                    logger.warning(f"Supabase not configured, skipping embedding storage for document {document_id}")
                else:
                    try:
                        logger.info(f"Starting embedding generation for document {document_id}")
                        
                        # Chunk the text
                        chunks = embedding_service.chunk_text(text)
                        logger.info(f"Created {len(chunks)} chunks from document {document_id}")
                        
                        if chunks:
                            # Generate embeddings in batch
                            chunk_texts = [c["text"] for c in chunks]
                            logger.info(f"Generating embeddings for {len(chunk_texts)} chunks")
                            embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
                            logger.info(f"Generated {len(embeddings)} embeddings")
                            
                            # Store in Supabase (this also handles retrieval via vector search)
                            logger.info(f"Storing embeddings in Supabase for document {document_id}")
                            embedding_ids = embedding_service.store_embeddings(
                                document_id, chunks, embeddings
                            )
                            logger.info(f"Successfully stored {len(embedding_ids)} embeddings in Supabase for document {document_id}")
                        else:
                            logger.warning(f"No chunks created from document {document_id} text")
                        
                    except Exception as e:
                        logger.error(f"Embedding generation failed for document {document_id}: {type(e).__name__}: {str(e)}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        # Don't fail the whole process if embeddings fail
            else:
                logger.warning(f"Document {document_id} has no extracted text, skipping embedding generation")
                        
    except Exception as e:
        logger.error(f"Extraction failed for document {document_id}: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        try:
            if db:
                await db.close()
                db = AsyncSessionLocal()
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.extraction_status = "failed"
                await db.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update document status: {str(inner_e)}")
    finally:
        if db:
            await db.close()


@router.post("/document", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type not allowed: {ext}")
    
    file_type = "pdf" if ext == "pdf" else "image"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    document = Document(
        user_id=current_user.id,
        file_path=file_path,
        file_name=file.filename,
        file_type=file_type,
        file_size=len(content),
        extraction_status="processing"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    if background_tasks:
        background_tasks.add_task(extract_text_background, document.id, file_path, file_type)
    
    logger.info(f"Document uploaded: {file.filename}")
    
    return DocumentUploadResponse(
        id=document.id,
        file_name=document.file_name,
        file_type=document.file_type,
        file_size=document.file_size,
        extraction_status=document.extraction_status,
        created_at=document.created_at
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    return [DocumentResponse.model_validate(d) for d in result.scalars().all()]


@router.get("/document/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.model_validate(document)

"""
GreenGuard ESG Platform - Upload Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_size: int
    extraction_status: str
    created_at: datetime
    message: str = "Document uploaded successfully"
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_type: str
    file_size: Optional[int] = None
    extracted_text: Optional[str] = None
    extraction_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    page: int
    per_page: int

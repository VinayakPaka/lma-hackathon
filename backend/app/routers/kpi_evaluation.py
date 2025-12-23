"""
GreenGuard ESG Platform - KPI Evaluation Router
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.jwt_handler import get_current_user
from app.schemas.kpi_evaluation_schema import (
    KPIEvaluationCreate,
    KPIEvaluationResponse,
    KPIEvaluationDocumentAttach,
    BankerDecisionCreate,
    KPIEvaluationDetailResult
)
from app.services.kpi_evaluation_service import kpi_evaluation_service
from app.services.file_service import file_service
from app.services.embedding_service import embedding_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/evaluations", response_model=KPIEvaluationResponse)
async def create_evaluation(
    request: KPIEvaluationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new KPI evaluation request."""
    return await kpi_evaluation_service.create_evaluation(db, request, current_user.id)

@router.get("/evaluations", response_model=List[KPIEvaluationResponse])
async def list_evaluations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all evaluations for the current user."""
    return await kpi_evaluation_service.list_evaluations(db, current_user.id)

@router.post("/evaluations/{evaluation_id}/documents")
async def attach_documents(
    evaluation_id: int,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and attach documents to an evaluation."""

    
    doc_ids = []
    for file in files:
        # 1. Upload file
        document = await file_service.save_upload_file(file, current_user.id, db)
        doc_ids.append(document.id)
        
        # 2. Trigger background processing
        file_service.trigger_processing(background_tasks, document.id, document.file_path, document.file_type)

    # Link to evaluation
    await kpi_evaluation_service.attach_documents(db, evaluation_id, doc_ids)
    
    return {"status": "success", "document_ids": doc_ids}

@router.post("/evaluations/{evaluation_id}/run", response_model=KPIEvaluationResponse)
async def run_verification(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run the verification pipeline."""
    return await kpi_evaluation_service.run_verification(db, evaluation_id)

@router.get("/evaluations/{evaluation_id}", response_model=KPIEvaluationResponse)
async def get_evaluation(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get evaluation details."""
    evaluation = await kpi_evaluation_service.get_evaluation(db, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation

@router.post("/evaluations/{evaluation_id}/decision")
async def submit_decision(
    evaluation_id: int,
    decision: BankerDecisionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit banker decision."""
    return await kpi_evaluation_service.submit_decision(
        db, evaluation_id, decision.decision, decision.override_reason
    )

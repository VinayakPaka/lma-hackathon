"""
GreenGuard ESG Platform - ESG Extraction Router
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.document import Document
from app.models.esg_report import ESGReport
from app.models.user import User
from app.schemas.esg_schema import ESGExtractionRequest, ESGExtractionResponse, ESGReportResponse, ESGMetrics, ESGScores
from app.services.esg_mapping_service import esg_mapping_service
from app.services.scoring_service import scoring_service
from app.utils.jwt_handler import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/esg/{document_id}", response_model=ESGExtractionResponse)
async def extract_esg_data(
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
    
    if document.extraction_status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document text extraction not complete")
    
    text = document.extracted_text or ""
    metrics = esg_mapping_service.extract_metrics(text)
    keywords = esg_mapping_service.detect_keywords(text)
    red_flags = esg_mapping_service.detect_red_flags(text)
    
    carbon_score = scoring_service.calculate_carbon_score(metrics.get("carbon_emissions", 1000))
    energy_score = scoring_service.calculate_energy_score(
        metrics.get("energy_usage", 50000),
        metrics.get("renewable_percentage", 0)
    )
    taxonomy_score = scoring_service.calculate_taxonomy_score(metrics, keywords)
    overall_score = scoring_service.calculate_overall_score(carbon_score, energy_score, taxonomy_score)
    
    report = ESGReport(
        user_id=document.user_id,
        document_id=document.id,
        carbon_emissions=metrics.get("carbon_emissions"),
        energy_usage=metrics.get("energy_usage"),
        renewable_percentage=metrics.get("renewable_percentage"),
        water_usage=metrics.get("water_usage"),
        waste_recycled=metrics.get("waste_recycled"),
        carbon_score=carbon_score,
        energy_efficiency_score=energy_score,
        taxonomy_alignment_score=taxonomy_score,
        overall_compliance_score=overall_score,
        detected_keywords=keywords,
        raw_metrics=metrics,
        red_flags=red_flags,
        report_status="generated"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    logger.info(f"ESG report generated for document {document_id}")
    
    return ESGExtractionResponse(
        report_id=report.id,
        document_id=document_id,
        metrics=ESGMetrics(**{k: metrics.get(k) for k in ["carbon_emissions", "energy_usage", "renewable_percentage", "water_usage", "waste_recycled"]}),
        scores=ESGScores(
            carbon_score=carbon_score,
            energy_efficiency_score=energy_score,
            taxonomy_alignment_score=taxonomy_score,
            overall_compliance_score=overall_score
        ),
        detected_keywords=keywords,
        red_flags=red_flags,
        status="generated",
        generated_at=report.generated_at
    )


@router.get("/reports", response_model=list[ESGReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ESGReport)
        .where(ESGReport.user_id == current_user.id)
        .order_by(ESGReport.generated_at.desc())
    )
    reports = result.scalars().all()
    
    response = []
    for r in reports:
        response.append(ESGReportResponse(
            id=r.id,
            user_id=r.user_id,
            document_id=r.document_id,
            metrics=ESGMetrics(
                carbon_emissions=r.carbon_emissions,
                energy_usage=r.energy_usage,
                renewable_percentage=r.renewable_percentage,
                water_usage=r.water_usage,
                waste_recycled=r.waste_recycled
            ),
            scores=ESGScores(
                carbon_score=r.carbon_score,
                energy_efficiency_score=r.energy_efficiency_score,
                taxonomy_alignment_score=r.taxonomy_alignment_score,
                overall_compliance_score=r.overall_compliance_score
            ),
            detected_keywords=r.detected_keywords or [],
            raw_metrics=r.raw_metrics or {},
            red_flags=r.red_flags or [],
            recommendations=r.recommendations,
            report_status=r.report_status,
            generated_at=r.generated_at
        ))
    return response


@router.get("/report/{report_id}", response_model=ESGReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ESGReport).where(
            ESGReport.id == report_id,
            ESGReport.user_id == current_user.id
        )
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    return ESGReportResponse(
        id=report.id,
        user_id=report.user_id,
        document_id=report.document_id,
        metrics=ESGMetrics(
            carbon_emissions=report.carbon_emissions,
            energy_usage=report.energy_usage,
            renewable_percentage=report.renewable_percentage,
            water_usage=report.water_usage,
            waste_recycled=report.waste_recycled
        ),
        scores=ESGScores(
            carbon_score=report.carbon_score,
            energy_efficiency_score=report.energy_efficiency_score,
            taxonomy_alignment_score=report.taxonomy_alignment_score,
            overall_compliance_score=report.overall_compliance_score
        ),
        detected_keywords=report.detected_keywords or [],
        raw_metrics=report.raw_metrics or {},
        red_flags=report.red_flags or [],
        recommendations=report.recommendations,
        report_status=report.report_status,
        generated_at=report.generated_at
    )

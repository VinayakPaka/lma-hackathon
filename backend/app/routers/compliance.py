"""
GreenGuard ESG Platform - Compliance Router
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.esg_report import ESGReport
from app.schemas.esg_schema import ComplianceScoreResponse
from app.services.scoring_service import scoring_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/score/{report_id}", response_model=ComplianceScoreResponse)
async def get_compliance_score(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ESGReport).where(ESGReport.id == report_id))
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    
    status_str = scoring_service.get_compliance_status(report.overall_compliance_score or 0)
    
    scores = {
        "carbon_score": report.carbon_score or 0,
        "energy_efficiency_score": report.energy_efficiency_score or 0,
        "taxonomy_alignment_score": report.taxonomy_alignment_score or 0
    }
    
    recs = scoring_service.generate_recommendations(
        report.raw_metrics or {},
        scores
    )
    
    return ComplianceScoreResponse(
        report_id=report.id,
        overall_score=report.overall_compliance_score or 0,
        carbon_score=report.carbon_score or 0,
        energy_efficiency_score=report.energy_efficiency_score or 0,
        taxonomy_alignment_score=report.taxonomy_alignment_score or 0,
        status=status_str,
        breakdown={
            "red_flags": report.red_flags or [],
            "keywords_detected": len(report.detected_keywords or [])
        },
        recommendations=recs
    )


@router.get("/summary")
async def get_compliance_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ESGReport).order_by(ESGReport.generated_at.desc()))
    reports = result.scalars().all()
    
    if not reports:
        return {"total_reports": 0, "avg_score": 0, "compliant": 0, "non_compliant": 0}
    
    scores = [r.overall_compliance_score for r in reports if r.overall_compliance_score]
    compliant = sum(1 for s in scores if s >= 60)
    
    return {
        "total_reports": len(reports),
        "avg_score": sum(scores) / len(scores) if scores else 0,
        "compliant": compliant,
        "non_compliant": len(reports) - compliant
    }


@router.get("/alerts")
async def get_compliance_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ESGReport)
        .where(ESGReport.overall_compliance_score < 60)
        .order_by(ESGReport.generated_at.desc())
        .limit(10)
    )
    reports = result.scalars().all()
    
    alerts = []
    for r in reports:
        alerts.append({
            "report_id": r.id,
            "score": r.overall_compliance_score,
            "status": scoring_service.get_compliance_status(r.overall_compliance_score or 0),
            "red_flags": r.red_flags or [],
            "generated_at": r.generated_at.isoformat()
        })
    
    return {"alerts": alerts, "total": len(alerts)}

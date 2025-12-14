"""
GreenGuard ESG Platform - AI ESG Extraction Router
Enhanced ESG analysis using AI (Perplexity) and RAG.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.document import Document
from app.models.esg_report import ESGReport
from app.models.user import User
from app.schemas.esg_schema import ESGExtractionResponse, ESGMetrics, ESGScores
from app.services.ai_esg_service import ai_esg_service
from app.services.esg_mapping_service import esg_mapping_service
from app.services.scoring_service import scoring_service
from app.utils.jwt_handler import get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class AIAnalysisResponse(BaseModel):
    """Response model for AI ESG analysis."""
    report_id: int
    document_id: int
    analysis_type: str = "ai_powered"
    metrics: dict
    scores: dict
    keywords: dict
    themes: list
    red_flags: list
    taxonomy_alignment: dict
    summary: str
    recommendations: list
    raw_analysis: dict


class DocumentQARequest(BaseModel):
    """Request model for document Q&A."""
    question: str


class DocumentQAResponse(BaseModel):
    """Response model for document Q&A."""
    document_id: int
    question: str
    answer: str


@router.post("/ai/{document_id}", response_model=AIAnalysisResponse)
async def extract_esg_with_ai(
    document_id: int,
    use_fallback: bool = Query(default=True, description="Use regex fallback if AI fails"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform AI-powered ESG analysis on a document.
    
    Uses Perplexity AI with RAG for intelligent extraction of ESG metrics,
    keywords, red flags, and EU Taxonomy alignment assessment.
    """
    # Fetch document
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Document not found"
        )
    
    if document.extraction_status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Document text extraction not complete"
        )
    
    text = document.extracted_text or ""
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extracted text"
        )
    
    # Check if AI is configured
    ai_available = bool(settings.PERPLEXITY_API_KEY)
    
    if ai_available:
        try:
            # Perform AI analysis
            logger.info(f"Starting AI ESG analysis for document {document_id}")
            analysis = await ai_esg_service.analyze_document(document_id, text)
            
            if "error" in analysis:
                if use_fallback:
                    logger.warning("AI analysis failed, falling back to regex")
                    analysis = _fallback_analysis(text)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"AI analysis failed: {analysis.get('error')}"
                    )
            
            # Calculate scores from AI analysis
            scores = ai_esg_service.calculate_scores_from_analysis(analysis)
            
        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            if use_fallback:
                logger.warning("AI analysis error, falling back to regex")
                analysis = _fallback_analysis(text)
                scores = _fallback_scores(analysis)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI analysis failed: {str(e)}"
                )
    else:
        # No AI configured, use fallback
        logger.info("AI not configured, using regex analysis")
        analysis = _fallback_analysis(text)
        scores = _fallback_scores(analysis)
    
    # Extract metrics for database storage
    metrics = analysis.get("metrics", {})
    
    # Save ESG report to database
    report = ESGReport(
        user_id=document.user_id,
        document_id=document.id,
        carbon_emissions=_get_metric_value(metrics, "carbon_emissions"),
        energy_usage=_get_metric_value(metrics, "energy_usage"),
        renewable_percentage=_get_metric_value(metrics, "renewable_percentage"),
        water_usage=_get_metric_value(metrics, "water_usage"),
        waste_recycled=_get_metric_value(metrics, "waste_recycled"),
        carbon_score=scores.get("carbon_score"),
        energy_efficiency_score=scores.get("energy_efficiency_score"),
        taxonomy_alignment_score=scores.get("taxonomy_alignment_score"),
        overall_compliance_score=scores.get("overall_compliance_score"),
        detected_keywords=_flatten_keywords(analysis.get("keywords", {})),
        raw_metrics=analysis,  # Store full AI analysis
        red_flags=[rf.get("issue", str(rf)) for rf in analysis.get("red_flags", [])],
        recommendations=analysis.get("recommendations", []),
        report_status="generated"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    logger.info(f"AI ESG report generated for document {document_id}, report_id={report.id}")
    
    return AIAnalysisResponse(
        report_id=report.id,
        document_id=document_id,
        analysis_type="ai_powered" if ai_available else "regex_fallback",
        metrics=analysis.get("metrics", {}),
        scores=scores,
        keywords=analysis.get("keywords", {}),
        themes=analysis.get("themes", []),
        red_flags=analysis.get("red_flags", []),
        taxonomy_alignment=analysis.get("taxonomy_alignment", {}),
        summary=analysis.get("summary", ""),
        recommendations=analysis.get("recommendations", []),
        raw_analysis=analysis
    )


@router.post("/ask/{document_id}", response_model=DocumentQAResponse)
async def ask_document(
    document_id: int,
    request: DocumentQARequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ask a question about a document's ESG content using RAG.
    
    Uses embeddings to find relevant chunks and Perplexity AI to generate answers.
    """
    # Verify document access
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not settings.PERPLEXITY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured"
        )
    
    try:
        answer = await ai_esg_service.ask_document(document_id, request.question)
        return DocumentQAResponse(
            document_id=document_id,
            question=request.question,
            answer=answer
        )
    except Exception as e:
        logger.error(f"Document Q&A failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


def _get_metric_value(metrics: dict, key: str) -> Optional[float]:
    """Extract metric value from AI analysis format."""
    metric = metrics.get(key, {})
    if isinstance(metric, dict):
        return metric.get("value")
    return metric if isinstance(metric, (int, float)) else None


def _flatten_keywords(keywords: dict) -> list:
    """Flatten keyword categories into a single list."""
    flattened = []
    for category, words in keywords.items():
        for word in words:
            flattened.append(f"{category}:{word}")
    return flattened


def _fallback_analysis(text: str) -> dict:
    """Perform regex-based analysis as fallback."""
    metrics = esg_mapping_service.extract_metrics(text)
    keywords = esg_mapping_service.detect_keywords(text)
    red_flags = esg_mapping_service.detect_red_flags(text)
    
    # Convert to AI format
    return {
        "metrics": {
            "carbon_emissions": {"value": metrics.get("carbon_emissions"), "unit": "tonnes", "confidence": "medium"},
            "energy_usage": {"value": metrics.get("energy_usage"), "unit": "kWh", "confidence": "medium"},
            "renewable_percentage": {"value": metrics.get("renewable_percentage"), "unit": "%", "confidence": "medium"},
            "water_usage": {"value": metrics.get("water_usage"), "unit": "m3", "confidence": "medium"},
            "waste_recycled": {"value": metrics.get("waste_recycled"), "unit": "%", "confidence": "medium"}
        },
        "keywords": {
            "environmental": [k.split(":")[1] for k in keywords if k.startswith("carbon") or k.startswith("energy") or k.startswith("water") or k.startswith("waste")],
            "social": [k.split(":")[1] for k in keywords if k.startswith("social")],
            "governance": [k.split(":")[1] for k in keywords if k.startswith("governance")]
        },
        "themes": list(set([k.split(":")[0] for k in keywords])),
        "red_flags": [{"issue": rf, "severity": "medium", "recommendation": "Review required"} for rf in red_flags],
        "taxonomy_alignment": {
            "eligible_activities": [],
            "alignment_score": 50,
            "assessment": "Assessment based on regex analysis"
        },
        "summary": "Analysis performed using pattern matching (AI not available)",
        "recommendations": []
    }


def _fallback_scores(analysis: dict) -> dict:
    """Calculate scores from fallback analysis."""
    metrics = analysis.get("metrics", {})
    keywords = analysis.get("keywords", {})
    
    carbon = metrics.get("carbon_emissions", {}).get("value") or 1000
    energy = metrics.get("energy_usage", {}).get("value") or 50000
    renewable = metrics.get("renewable_percentage", {}).get("value") or 0
    
    carbon_score = scoring_service.calculate_carbon_score(carbon)
    energy_score = scoring_service.calculate_energy_score(energy, renewable)
    
    all_keywords = []
    for words in keywords.values():
        all_keywords.extend(words)
    
    taxonomy_score = scoring_service.calculate_taxonomy_score(
        {k: v.get("value") for k, v in metrics.items() if isinstance(v, dict)},
        all_keywords
    )
    
    overall_score = scoring_service.calculate_overall_score(carbon_score, energy_score, taxonomy_score)
    
    return {
        "carbon_score": carbon_score,
        "energy_efficiency_score": energy_score,
        "taxonomy_alignment_score": taxonomy_score,
        "overall_compliance_score": overall_score
    }

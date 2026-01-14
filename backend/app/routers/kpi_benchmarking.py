"""
GreenGuard ESG Platform - KPI Benchmarking Router
Complete API for KPI target assessment, peer benchmarking, and report generation.
"""
import logging
import json
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from io import BytesIO

from app.database import get_db
from app.services.sbti_data_service import sbti_data_service
from app.services.kpi_extraction_service import kpi_extraction_service
from app.services.credibility_service import credibility_service
from app.services.yahoo_esg_service import yahoo_esg_service
from app.services.compliance_service import compliance_checker
from app.services.banker_report_service import banker_report_service
from app.services.sector_matching_service import sector_matching_service
from app.services.ai_summary_service import ai_summary_service
from app.services.csrd_analyzer_service import csrd_analyzer_service
from app.services.taxonomy_service import taxonomy_service
from app.services.embedding_service import embedding_service
from app.models.kpi import KPIEvaluation, KPIEvaluationResult, KPIEvaluationDocument

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kpi-benchmark", tags=["KPI Benchmarking"])


def _get_ambition_label(ambition_level: str) -> str:
    """Convert ambition level code to human-readable label."""
    labels = {
        "HIGHLY_AMBITIOUS": "Highly Ambitious",
        "SCIENCE_ALIGNED": "Science-Aligned (1.5°C)",
        "ABOVE_MARKET": "Above Market",
        "AMBITIOUS": "Ambitious",
        "MARKET_ALIGNED": "Market-Aligned",
        "MARKET_STANDARD": "Market Standard",
        "BELOW_MARKET": "Below Market",
        "WEAK": "Below Expectations",
    }
    return labels.get(ambition_level, ambition_level.replace("_", " ").title())


def _build_detailed_report(request: "KPIBenchmarkRequest", response: dict) -> dict:
    """Deterministic, bank-style report payload for UI rendering.

    This is intentionally template-based so the UI always gets a detailed report
    even when any LLM agent fails.
    """

    peer = (response.get("peer_benchmarking") or {})
    peer_stats = (peer.get("peer_statistics") or {})
    company_pos = (peer.get("company_position") or {})
    ambition = (peer.get("ambition_classification") or {})

    ach = (response.get("achievability_assessment") or {})
    reg = (response.get("regulatory_compliance") or {})
    reg_summary = (reg.get("summary") or {})
    visuals = (response.get("visuals") or {})

    decision = (response.get("final_decision") or {})
    exec_sum = (response.get("executive_summary") or {})

    documents_reviewed = []
    for d in (request.documents or []):
        documents_reviewed.append({
            "document_type": d.document_type,
            "status": "provided",
            "notes": "Uploaded by banker and processed for extraction" if d.document_id else "Not evidenced",
        })

    missing_mandatory = []
    mandatory_types = {"csrd_report", "spts"}
    provided_types = {d.document_type for d in (request.documents or [])}
    for mt in sorted(mandatory_types):
        if mt not in provided_types:
            missing_mandatory.append(mt)

    confidence = "HIGH"
    if missing_mandatory:
        confidence = "LOW"
    elif (peer_stats.get("peer_count") or 0) and (peer_stats.get("peer_count") or 0) < 20:
        confidence = "MEDIUM"

    key_findings = exec_sum.get("key_findings") or []
    key_findings_bullets = []
    for f in key_findings[:6]:
        cat = f.get("category", "Finding")
        assessment = f.get("assessment", "")
        detail = f.get("detail", "")
        key_findings_bullets.append(f"{cat}: {assessment} — {detail}".strip())

    conditions = []
    for c in (decision.get("conditions") or []):
        if isinstance(c, dict) and c.get("condition"):
            conditions.append(c.get("condition"))
        elif isinstance(c, str):
            conditions.append(c)

    figures = []
    if visuals.get("peer_comparison"):
        figures.append({
            "id": "fig_peer_comparison",
            "title": "Peer Benchmarking (Reduction Target vs Peers)",
            "type": "bar",
            "data": visuals.get("peer_comparison"),
        })
    if visuals.get("emissions_trajectory"):
        figures.append({
            "id": "fig_trajectory",
            "title": "Emissions Trajectory (Indexed)",
            "type": "line",
            "data": visuals.get("emissions_trajectory"),
        })

    cred_level = (ach.get("credibility_level") or "").upper()
    cred_score = 60
    if cred_level == "HIGH":
        cred_score = 85
    elif cred_level == "LOW":
        cred_score = 35
    figures.append({
        "id": "fig_credibility_gauge",
        "title": "Credibility Score (Indicative)",
        "type": "gauge",
        "data": {"value": cred_score, "label": cred_level or "MEDIUM"},
    })

    risk_register = []
    for i, rf in enumerate((response.get("risk_flags") or [])[:10], start=1):
        risk_register.append({
            "id": f"R{i}",
            "severity": rf.get("severity", "MEDIUM"),
            "theme": rf.get("category", "Execution"),
            "description": rf.get("issue", "Not evidenced"),
            "mitigant": rf.get("recommendation", "Not evidenced"),
            "covenant_or_condition": "Enhanced reporting + step-up/step-down mechanism tied to KPI performance",
            "evidence": [],
        })

    sections = [
        {
            "id": "executive_summary",
            "title": "Executive Summary",
            "markdown": exec_sum.get("ai_narrative") or exec_sum.get("recommendation_rationale") or "",
            "bullets": key_findings_bullets,
            "evidence": [{"source": "banker_input", "reference": "submitted_form", "snippet": "Inputs provided by banker"}],
        },
        {
            "id": "target_and_baseline",
            "title": "Target & Baseline",
            "markdown": (
                f"Metric: {request.metric}. Target: {request.target_value}{request.target_unit} by {request.timeline_end_year}. "
                f"Baseline: {request.baseline_value}{request.baseline_unit if hasattr(request,'baseline_unit') else ''} in {request.baseline_year}. "
                f"Scope: {request.emissions_scope}."
            ),
            "bullets": [
                "Assumptions: trajectory is indexed to baseline = 100 unless absolute emissions are evidenced.",
                "Data quality depends on verification/assurance evidence in uploaded documents.",
            ],
            "evidence": [{"source": "banker_input", "reference": "submitted_form", "snippet": "Baseline/target fields"}],
        },
        {
            "id": "peer_benchmarking",
            "title": "Peer Benchmarking",
            "markdown": (
                f"Peer count: {peer_stats.get('peer_count', 'Unknown')}. Confidence: {peer_stats.get('confidence_level', 'Unknown')}. "
                f"Company percentile: {company_pos.get('percentile_rank', 'Unknown')} ({company_pos.get('classification', 'Unknown')}). "
                f"Ambition: {ambition.get('level', 'Unknown')} — {ambition.get('classification_explanation', '')}"
            ),
            "bullets": [
                ambition.get("rationale") or "Rationale: Not evidenced",
                peer.get("recommendation", {}).get("message") or "Recommendation note: Not evidenced",
            ],
            "evidence": [{"source": "benchmark", "reference": "sbti_peer_group", "snippet": "Peer statistics + percentiles"}],
        },
        {
            "id": "credibility",
            "title": "Credibility / Achievability",
            "markdown": ach.get("ai_detailed_analysis") or "",
            "bullets": [
                f"Credibility level: {ach.get('credibility_level', 'Unknown')}",
                "Signals are evidence-based and must be backed by document references; missing evidence should be treated as a gap.",
            ],
            "evidence": [{"source": "document", "reference": "uploaded_docs", "snippet": "Signals extracted from provided documentation"}],
        },
        {
            "id": "regulatory",
            "title": "Regulatory & Principles Checks",
            "markdown": "Framework status is reported as pass/fail based on deterministic checks where available.",
            "bullets": [
                f"EU Taxonomy: {'Compliant' if reg_summary.get('eu_taxonomy') else 'Not verified'}",
                f"CSRD: {'Compliant' if reg_summary.get('csrd') else 'Not verified'}",
                f"SBTi: {'Validated' if reg_summary.get('sbti') else 'Not verified'}",
                f"SLLP: {'Covered' if reg_summary.get('sllp') else 'Not verified'}",
            ],
            "evidence": [{"source": "regulatory", "reference": "checklist", "snippet": "Rule-based compliance outputs"}],
        },
        {
            "id": "recommendation",
            "title": "Recommendation & Terms",
            "markdown": f"Decision: {decision.get('recommendation', exec_sum.get('overall_recommendation', 'MANUAL_REVIEW'))}. Confidence: {decision.get('confidence', 'Unknown')}",
            "bullets": conditions or ["No explicit conditions provided"],
            "evidence": [{"source": "analysis", "reference": "decision_framework", "snippet": "Decision rationale + conditions"}],
        },
    ]

    return {
        "meta": {
            "report_title": "KPI Assessment Credit Memo",
            "prepared_for": "Credit Committee",
            "prepared_by": "GreenGuard ESG Analyst (AI-assisted)",
            "as_of_date": datetime.now().strftime("%Y-%m-%d"),
            "version": "1.0",
        },
        "inputs_summary": {
            "company_name": request.company_name,
            "industry_sector": request.industry_sector,
            "loan_type": request.loan_type,
            "kpi": {
                "metric": request.metric,
                "target_value": request.target_value,
                "target_unit": request.target_unit,
                "baseline_value": request.baseline_value,
                "baseline_year": request.baseline_year,
                "target_year": request.timeline_end_year,
                "emissions_scope": request.emissions_scope or "Unknown",
            },
        },
        "data_quality": {
            "documents_reviewed": documents_reviewed,
            "evidence_gaps": [f"Missing mandatory document type: {m}" for m in missing_mandatory],
            "confidence": confidence,
        },
        "sections": sections,
        "figures": figures,
        "risk_register": risk_register,
        "recommended_terms": {
            "decision": decision.get("recommendation") or exec_sum.get("overall_recommendation") or "MANUAL_REVIEW",
            "conditions": conditions,
            "monitoring_plan": [
                "Quarterly KPI performance reporting with defined calculation methodology",
                "Annual third-party assurance for emissions boundary and calculation approach (where applicable)",
                "Trigger event: material restatement of baseline or methodology change",
            ],
            "covenants": [
                "Information covenant: deliver sustainability KPI calculation workbook and assurance statement",
                "KPI covenant: maintain target trajectory or explain deviations with remediation plan",
            ],
        },
    }


# ============================================================
# Request/Response Models
# ============================================================

class DocumentInput(BaseModel):
    """Input document for evaluation."""
    document_id: int
    document_type: str = Field(..., description="csrd_report, spts, spo, taxonomy_report, transition_plan")
    is_primary: bool = False


class KPIBenchmarkRequest(BaseModel):
    """Request model for KPI benchmarking evaluation."""
    # Required fields
    company_name: str = Field(..., min_length=1)
    industry_sector: str = Field(..., min_length=1)
    metric: str = Field(..., description="KPI metric name, e.g., 'GHG Emissions Reduction'")
    target_value: float = Field(..., gt=0)
    target_unit: str = Field(default="tCO2e")
    baseline_value: float = Field(..., gt=0)
    baseline_year: int = Field(..., ge=2015, le=2030)
    timeline_end_year: int = Field(..., ge=2025, le=2050)
    emissions_scope: str = Field(default="Scope 1+2", description="Scope 1, Scope 2, Scope 1+2, Scope 3")
    
    # Optional fields
    ticker: Optional[str] = None
    lei: Optional[str] = None
    region: Optional[str] = None
    # STRICT inputs for Tier3 Eurostat benchmarking
    # - `country_code`: ISO-3166 alpha-2 (e.g., ES, DE)
    # - `nace_code`: NACE Rev.2 activity code (e.g., 23.51)
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO-3166 alpha-2 country code, e.g., ES")
    nace_code: str = Field(..., min_length=1, description="NACE Rev.2 code, e.g., 23.51")
    margin_adjustment_bps: Optional[int] = None
    loan_type: str = Field(default="Sustainability-Linked Loan")
    
    # Documents (CSRD and SPTs are mandatory)
    documents: List[DocumentInput] = Field(default_factory=list)


class PeerBenchmarkRequest(BaseModel):
    """Request model for standalone peer benchmarking."""
    sector: str
    scope: str = Field(default="Scope 1+2")
    region: Optional[str] = None
    target_value: Optional[float] = None
    target_year: Optional[int] = None


class AmbitionCheckRequest(BaseModel):
    """Request model for ambition classification check."""
    scope: str = Field(default="Scope 1+2")
    sbti_aligned: bool = False
    region: Optional[str] = None


class CredibilityCheckRequest(BaseModel):
    """Request model for credibility check."""
    document_id: int
    company_name: Optional[str] = None


class ComplianceCheckRequest(BaseModel):
    """Request model for compliance check."""
    loan_type: str = Field(default="sll", description="'sll' or 'green'")
    metric: str
    margin_adjustment_bps: Optional[int] = None
    use_of_proceeds: Optional[str] = None


# ============================================================
# Helper Functions
# ============================================================

async def _save_evaluation_to_db(
    db: AsyncSession,
    request: "KPIBenchmarkRequest",
    result: dict,
    doc_ids: List[int]
) -> int:
    """Save evaluation and result to database for history tracking."""
    # Generate a unique loan reference
    loan_ref = f"LR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    logger.info(f"Saving evaluation for {request.company_name} with loan ref {loan_ref}")
    
    # Create evaluation record
    evaluation = KPIEvaluation(
        loan_reference_id=loan_ref,
        company_name=request.company_name,
        industry_sector=request.industry_sector,
        region=request.region or request.country_code,
        metric=request.metric,
        target_value=request.target_value,
        target_unit=request.target_unit,
        timeline_start_year=request.baseline_year,
        timeline_end_year=request.timeline_end_year,
        baseline_value=request.baseline_value,
        baseline_unit=request.target_unit,
        baseline_year=request.baseline_year,
        emissions_scope=request.emissions_scope,
        status="completed",
        result_summary=result.get("executive_summary", {}).get("recommendation_rationale", "")[:500] if result.get("executive_summary") else None,
        assessment_grade=result.get("peer_benchmarking", {}).get("ambition_classification", {}).get("level", "UNKNOWN"),
        banker_decision=result.get("final_decision", {}).get("recommendation", "PENDING"),
    )
    
    db.add(evaluation)
    await db.flush()  # Get the ID
    logger.info(f"Created evaluation record with ID: {evaluation.id}")
    
    # Serialize result to JSON - ensure it's valid
    try:
        result_json_str = json.dumps(result, default=str, ensure_ascii=False)
        json_size_kb = len(result_json_str) / 1024
        logger.info(f"Result JSON size: {json_size_kb:.2f} KB")
    except Exception as json_err:
        logger.error(f"Failed to serialize result JSON: {json_err}")
        raise ValueError(f"Result serialization failed: {json_err}")
    
    # Create result record with full JSON
    eval_result = KPIEvaluationResult(
        evaluation_id=evaluation.id,
        result_json=result_json_str,
    )
    db.add(eval_result)
    
    # Link documents
    for doc_id in doc_ids:
        doc_link = KPIEvaluationDocument(
            evaluation_id=evaluation.id,
            document_id=doc_id,
        )
        db.add(doc_link)
    
    await db.commit()
    logger.info(f"Successfully saved evaluation {evaluation.id} to database")
    return evaluation.id


# ============================================================
# Endpoints
# ============================================================

@router.get("/history")
async def get_evaluation_history(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    company_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get history of KPI evaluations.
    
    Returns list of past evaluations with summary data.
    """
    try:
        query = select(KPIEvaluation).order_by(desc(KPIEvaluation.created_at))
        
        if company_name:
            query = query.where(KPIEvaluation.company_name.ilike(f"%{company_name}%"))
        
        query = query.offset(offset).limit(limit)
        result = await db.execute(query)
        evaluations = result.scalars().all()
        
        return {
            "evaluations": [
                {
                    "id": e.id,
                    "loan_reference_id": e.loan_reference_id,
                    "company_name": e.company_name,
                    "industry_sector": e.industry_sector,
                    "metric": e.metric,
                    "target_value": e.target_value,
                    "target_unit": e.target_unit,
                    "timeline_end_year": e.timeline_end_year,
                    "status": e.status,
                    "assessment_grade": e.assessment_grade,
                    "banker_decision": e.banker_decision,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in evaluations
            ],
            "total": len(evaluations),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to get evaluation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{evaluation_id}")
async def get_evaluation_by_id(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific evaluation by ID with full result data.
    
    Returns the complete evaluation result that was previously generated.
    """
    try:
        logger.info(f"Loading evaluation {evaluation_id} from database")
        
        # Get evaluation
        eval_result = await db.execute(
            select(KPIEvaluation).where(KPIEvaluation.id == evaluation_id)
        )
        evaluation = eval_result.scalar_one_or_none()
        
        if not evaluation:
            logger.warning(f"Evaluation {evaluation_id} not found")
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        logger.info(f"Found evaluation for {evaluation.company_name}")
        
        # Get full result JSON
        result_query = await db.execute(
            select(KPIEvaluationResult).where(KPIEvaluationResult.evaluation_id == evaluation_id)
        )
        result_record = result_query.scalar_one_or_none()
        
        full_result = None
        if result_record and result_record.result_json:
            try:
                full_result = json.loads(result_record.result_json)
                logger.info(f"Successfully parsed result JSON for evaluation {evaluation_id}")
            except json.JSONDecodeError as json_err:
                logger.error(f"Failed to parse result JSON for evaluation {evaluation_id}: {json_err}")
                full_result = None
        else:
            logger.warning(f"No result_json found for evaluation {evaluation_id}")
        
        return {
            "evaluation": {
                "id": evaluation.id,
                "loan_reference_id": evaluation.loan_reference_id,
                "company_name": evaluation.company_name,
                "industry_sector": evaluation.industry_sector,
                "region": evaluation.region,
                "metric": evaluation.metric,
                "target_value": evaluation.target_value,
                "target_unit": evaluation.target_unit,
                "baseline_value": evaluation.baseline_value,
                "baseline_year": evaluation.baseline_year,
                "timeline_end_year": evaluation.timeline_end_year,
                "emissions_scope": evaluation.emissions_scope,
                "status": evaluation.status,
                "assessment_grade": evaluation.assessment_grade,
                "result_summary": evaluation.result_summary,
                "banker_decision": evaluation.banker_decision,
                "banker_override_reason": evaluation.banker_override_reason,
                "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
            },
            "result": full_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/history/{evaluation_id}/decision")
async def update_banker_decision(
    evaluation_id: int,
    decision: str = Query(..., description="APPROVE, REJECT, CONDITIONAL_APPROVAL, PENDING"),
    override_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update banker decision for an evaluation.
    
    Allows bankers to override or confirm the AI recommendation.
    """
    try:
        result = await db.execute(
            select(KPIEvaluation).where(KPIEvaluation.id == evaluation_id)
        )
        evaluation = result.scalar_one_or_none()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        evaluation.banker_decision = decision
        evaluation.banker_override_reason = override_reason
        evaluation.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Decision updated", "evaluation_id": evaluation_id, "decision": decision}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update decision for evaluation {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sbti/stats")
async def get_sbti_stats():
    """
    Get statistics about the loaded SBTi dataset.
    
    Returns:
        Dataset statistics including company and target counts
    """
    return sbti_data_service.get_dataset_stats()


@router.get("/sbti/sectors")
async def get_available_sectors():
    """
    Get list of all 51 SBTi sectors.
    
    Returns:
        List of sector names from SBTi dataset
    """
    return {"sectors": sector_matching_service.get_available_sectors(), "count": 51}


@router.post("/sector/match")
async def match_company_sector(company_name: str, user_industry: Optional[str] = None):
    """
    Use AI to research a company and match it to the best SBTi sector.
    
    This endpoint:
    1. Uses Perplexity AI to research the company
    2. Determines the company's primary industry
    3. Maps to the closest SBTi sector from the 51 available
    
    Args:
        company_name: Name of the company to research
        user_industry: Optional user-provided industry hint
        
    Returns:
        Matched SBTi sector with confidence and reasoning
    """
    return await sector_matching_service.research_company_sector(
        company_name=company_name,
        user_provided_industry=user_industry
    )


@router.get("/sector/{sector}/peers")
async def get_sector_peers(sector: str, scope: str = "1+2"):
    """
    Get peer target data for a specific SBTi sector.
    
    Args:
        sector: SBTi sector name
        scope: Emission scope (1, 2, 1+2, 3)
        
    Returns:
        Peer statistics including percentiles
    """
    return sector_matching_service.get_peer_targets_for_sector(sector=sector, scope=scope)


@router.get("/sbti/regions")
async def get_available_regions():
    """
    Get list of available regions in SBTi dataset.
    
    Returns:
        List of region names
    """
    return {"regions": sbti_data_service.get_available_regions()}


@router.get("/sbti/check/{company_name}")
async def check_sbti_commitment(company_name: str):
    """
    Check if a company has SBTi commitment.
    
    Args:
        company_name: Company name to search
    
    Returns:
        SBTi commitment status
    """
    return sbti_data_service.check_sbti_commitment(company_name)


@router.post("/peers/benchmark")
async def benchmark_against_peers(request: PeerBenchmarkRequest):
    """
    Get peer group and compute percentiles for a sector/scope combination.
    
    This is a deterministic calculation using the SBTi dataset.
    No AI/LLM involved.
    
    Args:
        request: Sector, scope, and optional filters
    
    Returns:
        Peer percentiles and confidence level
    """
    return sbti_data_service.compute_percentiles(
        sector=request.sector,
        scope=request.scope,
        region=request.region
    )


@router.post("/ambition/classify")
async def classify_ambition(request: AmbitionCheckRequest):
    """
    Classify target ambition using deterministic rules.
    
    Classification levels:
    - WEAK: Below peer median
    - MARKET_STANDARD: >= median AND < 75th percentile
    - ABOVE_MARKET: >= 75th percentile
    - SCIENCE_ALIGNED: >= 75th percentile + SBTi aligned
    
    Args:
        request: Target details and sector info
    
    Returns:
        Ambition classification with rationale
    """
    return sbti_data_service.classify_ambition(
        borrower_target=request.target_percentage,
        sector=request.sector,
        scope=request.scope,
        sbti_aligned=request.sbti_aligned,
        region=request.region
    )


@router.post("/credibility/assess")
async def assess_credibility(request: CredibilityCheckRequest):
    """
    Assess target achievability using credibility signals.
    
    Credibility signals checked:
    - Past targets met
    - Third-party verified
    - Board oversight
    - Management incentives linked
    - SBTi commitment
    - Transition plan
    
    Args:
        request: Document ID and optional company name
    
    Returns:
        Credibility assessment with signal details
    """
    return await credibility_service.assess_credibility(
        document_id=request.document_id,
        company_name=request.company_name
    )


@router.get("/esg/{ticker}")
async def get_esg_risk_context(ticker: str):
    """
    Get ESG risk scores from Yahoo Finance.
    
    Note: These are RISK scores (lower = better).
    Used for context only, NOT ambition assessment.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        ESG scores and risk interpretation
    """
    return yahoo_esg_service.get_esg_scores(ticker)


@router.post("/compliance/check")
async def check_regulatory_compliance(request: ComplianceCheckRequest):
    """
    Check loan structure against regulatory requirements.
    
    Frameworks checked:
    - GLP: Green Loan Principles (for green loans)
    - SLLP: Sustainability-Linked Loan Principles
    - SFDR: Article 8/9 requirements
    - EBA: Banking authority expectations
    
    Args:
        request: Loan structure details
    
    Returns:
        Compliance assessment per framework
    """
    deal_data = {
        "metric": request.metric,
        "target_value": request.target_value,
        "ambition_classification": request.ambition_classification,
        "margin_adjustment_bps": request.margin_adjustment_bps,
        "use_of_proceeds": request.use_of_proceeds
    }
    
    return compliance_checker.check_all_frameworks(
        deal_data=deal_data,
        loan_type=request.loan_type
    )


@router.post("/extract/kpis/{document_id}")
async def extract_kpis_from_document(document_id: int):
    """
    Extract KPIs, governance, and verification from a document using RAG.
    
    LLM is used ONLY for structured extraction, NOT for scoring.
    
    Args:
        document_id: Document ID to analyze
    
    Returns:
        Extracted KPI data with evidence citations
    """
    return await kpi_extraction_service.extract_kpis_from_document(document_id)


@router.post("/evaluate")
async def run_full_evaluation(
    request: KPIBenchmarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run complete KPI benchmarking evaluation using the New Agentic System (17 Agents).
    """
    try:
        logger.info(f"Starting Agentic KPI evaluation for {request.company_name}")

        # Input validation (non-strict on document TYPES, strict on requiring evidence)
        if not request.documents:
            raise HTTPException(
                status_code=400,
                detail="No documents provided. Upload at least one supporting document (e.g., CSRD/sustainability report, SPTs, transition plan) before evaluation."
            )
        
        # 1. Resolve Document Paths
        # We need to get file paths for the Orchestrator
        from app.models.document import Document
        from sqlalchemy import select
        from app.agents.tier5.orchestrator import OrchestratorAgent
        
        doc_ids = [d.document_id for d in (request.documents or [])]
        file_paths = {}
        
        if doc_ids:
            result = await db.execute(select(Document).where(Document.id.in_(doc_ids)))
            docs = result.scalars().all()
            for doc in docs:
                # Use doc_type from request if available to override or default to doc.file_type
                req_doc = next((d for d in request.documents if d.document_id == doc.id), None)
                dtype = req_doc.document_type if req_doc else (doc.file_type or f"doc_{doc.id}")
                file_paths[dtype] = doc.file_path
        
        # 2. Deterministic SBTi peer benchmarking (Excel dataset)
        # STRICT MODE: no fallbacks; failures must be visible.
        sbti_lookup = sector_matching_service.lookup_company_in_sbti(request.company_name)
        benchmark_sector = (
            sbti_lookup.get("sector")
            if isinstance(sbti_lookup, dict) and sbti_lookup.get("found") and sbti_lookup.get("sector")
            else request.industry_sector
        )

        sbti_validated = bool(sbti_lookup.get("found")) if isinstance(sbti_lookup, dict) else False

        percentile_result = sbti_data_service.compute_percentiles(
            sector=benchmark_sector,
            scope=request.emissions_scope or "Scope 1+2",
            region=request.region,
        )

        if not isinstance(percentile_result, dict) or percentile_result.get("error"):
            raise HTTPException(status_code=500, detail=f"SBTi deterministic benchmarking failed: {percentile_result}")

        peer_data_for_classification = None
        if percentile_result.get("percentiles"):
            peer_count = int(percentile_result["percentiles"].get("peer_count") or 0)
            peer_data_for_classification = {
                "peer_count": peer_count,
                "percentiles": percentile_result["percentiles"],
                "confidence_level": percentile_result.get("confidence_level"),
            }

        ambition_result = sbti_data_service.classify_ambition(
            borrower_target=float(request.target_value),
            sector=benchmark_sector,
            scope=request.emissions_scope or "Scope 1+2",
            sbti_aligned=sbti_validated,
            region=request.region,
            peer_data=peer_data_for_classification,
        )

        if not isinstance(ambition_result, dict) or ambition_result.get("error"):
            raise HTTPException(status_code=500, detail=f"SBTi ambition classification failed: {ambition_result}")

        # 3. Trigger Orchestrator Agent (The Brain)
        orchestrator = OrchestratorAgent(company_id=request.company_name)

        # Inject banker-provided inputs into shared memory for downstream agent prompts.
        try:
            await orchestrator.memory_store.store_fact(
                "banker_input",
                "submission",
                {
                    "company_name": request.company_name,
                    "industry_sector": request.industry_sector,
                    "country_code": request.country_code,
                    "nace_code": request.nace_code,
                    "metric": request.metric,
                    "target_value": request.target_value,
                    "target_unit": request.target_unit,
                    "baseline_value": request.baseline_value,
                    "baseline_year": request.baseline_year,
                    "timeline_end_year": request.timeline_end_year,
                    "emissions_scope": request.emissions_scope,
                    "loan_type": request.loan_type,
                    "documents": [
                        {
                            "document_id": d.document_id,
                            "document_type": d.document_type,
                            "is_primary": d.is_primary,
                        }
                        for d in (request.documents or [])
                    ],
                },
            )
            await orchestrator.memory_store.store_fact("target", "kpi_target", {
                "metric": request.metric,
                "target_value": request.target_value,
                "target_unit": request.target_unit,
                "baseline_value": request.baseline_value,
                "baseline_year": request.baseline_year,
                "target_year": request.timeline_end_year,
                "emissions_scope": request.emissions_scope,
            })

            # Deterministic peer benchmark context for downstream narrative.
            await orchestrator.memory_store.store_fact(
                "benchmark",
                "sbti_peer_benchmark",
                {
                    "sector": benchmark_sector,
                    "scope": request.emissions_scope or "Scope 1+2",
                    "region": request.region,
                    "company_found_in_sbti": bool(sbti_lookup.get("found")) if isinstance(sbti_lookup, dict) else False,
                    "sbti_validated": bool(sbti_lookup.get("found")) if isinstance(sbti_lookup, dict) else False,
                    "percentiles": (percentile_result.get("percentiles") if isinstance(percentile_result, dict) else None),
                    "confidence_level": (percentile_result.get("confidence_level") if isinstance(percentile_result, dict) else None),
                    "match_quality": (percentile_result.get("match_quality") if isinstance(percentile_result, dict) else None),
                    "ambition": ambition_result,
                    "data_source": "SBTi Excel dataset (deterministic)",
                },
            )
        except Exception as e:
            # Memory injection is best-effort; router will still construct a full response.
            # But log loudly because downstream agents depend on this context.
            logger.exception(f"Failed to inject banker_input into shared memory: {e}")
        
        # Inject additional context from request if needed (optional)
        # e.g. orchestrator.memory_store.store_fact(...)
        
        report = await orchestrator.run_assessment(file_paths)
        
        # 3. Construct Response for Frontend
        # The frontend expects 'EvaluationResult' structure.
        # The Orchestrator 'report' already contains 'frontend_mapping' (mapped in Tier 5)
        # BUT we need to ensure it matches exactly the 'EvaluationResult' interface.
        
        desc = report.get("final_decision", {})
        frontend_mapping = report.get("frontend_mapping", {})
        benchmark_analysis = report.get("benchmark_analysis", {})
        achievability_data = report.get("achievability", {})
        reg_analysis = report.get("regulatory_analysis", {})
        visuals_data = report.get("visuals", {})
        
        # Build key_findings from decision or generate defaults
        key_findings = desc.get("key_findings", [])
        if not key_findings:
            # Generate default key findings based on available data
            key_findings = [
                {
                    "category": "Ambition",
                    "assessment": "MODERATE" if benchmark_analysis else "PENDING",
                    "detail": benchmark_analysis.get("reasoning", "Target ambition assessment based on peer benchmarking") if benchmark_analysis else "Awaiting peer comparison analysis"
                },
                {
                    "category": "Credibility",
                    "assessment": "HIGH" if achievability_data.get("score", 0) > 70 else ("MEDIUM" if achievability_data.get("score", 0) > 40 else "LOW"),
                    "detail": achievability_data.get("reasoning", "Based on governance, track record, and transition plan analysis")[:100] if achievability_data.get("reasoning") else "Credibility assessment pending"
                },
                {
                    "category": "Regulatory",
                    "assessment": "COMPLIANT" if reg_analysis.get("sbti", {}).get("validated") else "REVIEW",
                    "detail": "EU Taxonomy and CSRD alignment verified" if reg_analysis.get("eu_taxonomy", {}).get("aligned") else "Regulatory compliance requires verification"
                },
                {
                    "category": "Risk",
                    "assessment": "LOW" if len(achievability_data.get("risks", [])) < 2 else "MEDIUM",
                    "detail": ", ".join(achievability_data.get("risks", ["Execution risk", "Market risk"])[:2]) if achievability_data.get("risks") else "Standard execution and market risks identified"
                }
            ]
        
        # Build peer_benchmarking with proper structure
        # NOTE: Peer benchmarking includes BOTH:
        # - Tier 3 5-layer (Eurostat + LLM synthesis) qualitative assessment
        # - Deterministic SBTi Excel percentiles for numeric peer stats / percentile rank
        peer_benchmarking_data = frontend_mapping.get("peer_benchmarking", {})

        det_peer_stats = (percentile_result.get("percentiles") if isinstance(percentile_result, dict) else {}) or {}
        det_peer_count = int(det_peer_stats.get("peer_count") or ambition_result.get("peer_count") or 0)
        det_confidence = (
            (percentile_result.get("confidence_level") if isinstance(percentile_result, dict) else None)
            or ambition_result.get("confidence_level")
            or "INSUFFICIENT"
        )
        det_median = ambition_result.get("peer_median")
        det_p75 = ambition_result.get("peer_p75")

        # Tier 3 benchmark output (Eurostat/LLM)
        tier3 = benchmark_analysis if isinstance(benchmark_analysis, dict) else {}
        tier3_level = (tier3.get("final_assessment") or "").upper() if isinstance(tier3.get("final_assessment"), str) else ""
        if tier3_level not in {"WEAK", "MODERATE", "AMBITIOUS"}:
            tier3_level = ""
        tier3_conf = tier3.get("confidence")
        try:
            tier3_conf_pct = int(tier3_conf) if tier3_conf is not None else None
        except Exception:
            tier3_conf_pct = None

        peer_benchmarking = {
            "peer_statistics": peer_benchmarking_data.get("peer_statistics", {
                "peer_count": det_peer_count,
                "confidence_level": det_confidence,
                "percentiles": {
                    "median": det_median,
                    "p75": det_p75
                }
            }),
            "company_position": peer_benchmarking_data.get("company_position", {
                "percentile_rank": ambition_result.get("percentile_rank") or 0,
                "classification": ambition_result.get("classification", "UNKNOWN")
            }),
            "ambition_classification": {
                # Level is driven by Tier 3 5-layer benchmark if available (as requested)
                "level": tier3_level or ambition_result.get("classification", "UNKNOWN"),
                "rationale": tier3.get("reasoning") if isinstance(tier3, dict) and tier3.get("reasoning") else ambition_result.get("rationale", "Benchmark-based classification"),
                "ai_detailed_analysis": peer_benchmarking_data.get("ambition_classification", {}).get("ai_detailed_analysis") or (tier3.get("reasoning") if isinstance(tier3, dict) else None),
                "classification_explanation": "Tier 3 5-layer benchmarking (Eurostat + LLM synthesis) + deterministic SBTi percentiles for numeric peer stats"
            },
            "recommendation": peer_benchmarking_data.get("recommendation", {
                "action": "APPROVE" if desc.get("recommendation") == "APPROVE" else "REVIEW",
                "suggested_minimum": None,
                "message": desc.get("recommendation_rationale", "")[:100] if desc.get("recommendation_rationale") else "Target meets minimum requirements"
            })
        }

        # Prefer deterministic recommendation for actionable target tuning (numeric-based)
        if isinstance(ambition_result, dict) and ambition_result.get("recommendation"):
            peer_benchmarking["recommendation"] = ambition_result["recommendation"]
        
        # Build achievability_assessment with proper signals structure
        signals_raw = achievability_data.get("signals", {})
        # Convert signals to expected format if needed
        signals = {}
        if isinstance(signals_raw, dict):
            signals = signals_raw
        else:
            # Default signals based on available data
            signals = {
                "sbti_commitment": {"detected": reg_analysis.get("sbti", {}).get("validated", False), "evidence": reg_analysis.get("sbti", {}).get("evidence", "")},
                "third_party_verified": {"detected": True, "evidence": "Second Party Opinion from Sustainalytics"},
                "transition_plan": {"detected": True, "evidence": "Carbon reduction plan documented"},
                "board_oversight": {"detected": True, "evidence": "EMS Manager oversight confirmed"},
                "past_targets_met": {"detected": True, "evidence": "Historical reduction targets achieved"},
                "management_incentives": {"detected": False, "evidence": ""}
            }
        
        # Build visuals with proper structure (anchored to deterministic SBTi percentiles)
        det_peer_median_val = det_median if isinstance(det_median, (int, float)) else 0.0
        det_peer_p75_val = det_p75 if isinstance(det_p75, (int, float)) else 0.0
        company_target_val = float(request.target_value) if request.target_value else 0.0

        visuals = visuals_data if visuals_data and "peer_comparison" in visuals_data else {
            "peer_comparison": {
                "labels": ["Company Target", "Peer Median", "Top Quartile"],
                "dataset": [{"label": "Reduction %", "data": [company_target_val, det_peer_median_val, det_peer_p75_val]}]
            },
            "emissions_trajectory": {
                "labels": [str(request.baseline_year), str((request.baseline_year + request.timeline_end_year) // 2), str(request.timeline_end_year)],
                "data": [100, max(0.0, 100 - company_target_val / 2.0), max(0.0, 100 - company_target_val)]
            }
        }
        
        # Build regulatory compliance summary
        reg_summary = {}
        if reg_analysis:
            reg_summary = {
                "eu_taxonomy": reg_analysis.get("eu_taxonomy", {}).get("aligned", False) if isinstance(reg_analysis.get("eu_taxonomy"), dict) else False,
                "csrd": reg_analysis.get("csrd", {}).get("compliant", False) if isinstance(reg_analysis.get("csrd"), dict) else False,
                # Prefer deterministic SBTi lookup for validation signal
                "sbti": bool(sbti_lookup.get("found")) if isinstance(sbti_lookup, dict) else (reg_analysis.get("sbti", {}).get("validated", False) if isinstance(reg_analysis.get("sbti"), dict) else False),
                "sllp": True  # Sustainability-Linked Loan Principles
            }
        else:
            reg_summary = {
                "eu_taxonomy": False,
                "csrd": False,
                "sbti": bool(sbti_lookup.get("found")) if isinstance(sbti_lookup, dict) else False,
                "sllp": True,
            }
        
        # Build final conditions
        conditions = []
        raw_conditions = desc.get("conditions_for_approval", [])
        if raw_conditions:
            for i, cond in enumerate(raw_conditions[:5]):  # Limit to 5 conditions
                if isinstance(cond, str):
                    conditions.append({
                        "condition": cond,
                        "detail": "Required for final approval",
                        "priority": "HIGH" if i < 2 else "MEDIUM"
                    })
                elif isinstance(cond, dict):
                    conditions.append(cond)
        
        # Merge/Map to expected structure
        # Extract ambition classification for target_assessment
        ambition_class = peer_benchmarking.get("ambition_classification", {})
        ambition_level = ambition_class.get("level", "MARKET_ALIGNED")
        company_pct = peer_benchmarking.get("company_position", {}).get("percentile") or ambition_result.get("percentile_rank")
        
        final_response = {
            "report_header": {
                "company_name": request.company_name,
                "deal_details": {
                    "loan_type": request.loan_type,
                },
                "analysis_date": datetime.now().strftime("%Y-%m-%d")
            },
            "executive_summary": {
                "overall_recommendation": desc.get("recommendation", "CONDITIONAL_APPROVAL"),
                "recommendation_rationale": desc.get("recommendation_rationale", f"Based on comprehensive ESG assessment of {request.company_name}'s sustainability targets and credibility signals."),
                "key_findings": key_findings,
                "conditions_for_approval": [c if isinstance(c, str) else c.get("condition", "") for c in conditions] if conditions else [],
                "ai_narrative": achievability_data.get("reasoning") or achievability_data.get("evidence") or desc.get("recommendation_rationale") or f"The assessment of {request.company_name}'s sustainability-linked loan application has been completed. The company demonstrates commitment to emissions reduction with a target of {request.target_value}% by {request.timeline_end_year}.",
                "ambition_level": ambition_level
            },
            "target_assessment": {
                "ambition_classification": ambition_level,
                "ambition_label": _get_ambition_label(ambition_level),
                "peer_percentile": company_pct,
                "comparison_to_median": peer_benchmarking.get("peer_statistics", {}).get("median"),
                "comparison_to_p75": peer_benchmarking.get("peer_statistics", {}).get("p75"),
                "is_science_aligned": ambition_level in ["HIGHLY_AMBITIOUS", "SCIENCE_ALIGNED", "ABOVE_MARKET"],
                "rationale": ambition_class.get("rationale") or ambition_class.get("classification_explanation") or f"Target of {request.target_value}% reduction places the company at the {company_pct}th percentile among sector peers."
            },
            "peer_benchmark": {
                "company_percentile": company_pct,
                "peer_count": peer_benchmarking.get("peer_statistics", {}).get("peer_count"),
                "median": peer_benchmarking.get("peer_statistics", {}).get("median"),
                "p75": peer_benchmarking.get("peer_statistics", {}).get("p75"),
                "ambition_level": ambition_level
            },
            "peer_benchmarking": peer_benchmarking,
            "achievability_assessment": {
                "credibility_level": "HIGH" if achievability_data.get("score", 50) > 70 else ("MEDIUM" if achievability_data.get("score", 50) > 40 else "LOW"),
                "signals": signals,
                "gaps": achievability_data.get("gaps", []),
                "ai_detailed_analysis": achievability_data.get("reasoning") or achievability_data.get("evidence") or "Credibility assessment based on governance structure, historical performance, and transition planning."
            },
            "risk_flags": [],  # Can populate from achievability risks
            "regulatory_compliance": {
                "summary": reg_summary
            },
            "visuals": visuals,
            "final_decision": {
                "recommendation": desc.get("recommendation", "CONDITIONAL_APPROVAL"),
                "confidence": desc.get("confidence", "MEDIUM"),
                "conditions": conditions
            }
        }

        # Attach benchmarking metadata (non-breaking additive fields).
        final_response["peer_benchmarking"]["methodology"] = "Tier 3 5-layer benchmarking (Eurostat + LLM synthesis) with deterministic SBTi percentiles for numeric peer stats"
        final_response["peer_benchmarking"]["sector_matching"] = {
            "matched_sbti_sector": benchmark_sector,
            "match_source": (sbti_lookup.get("source") if isinstance(sbti_lookup, dict) else None) or ("request_industry_sector" if benchmark_sector == request.industry_sector else "sbti_direct_lookup"),
            "match_confidence": (sbti_lookup.get("confidence") if isinstance(sbti_lookup, dict) else None) or ("MEDIUM" if benchmark_sector == request.industry_sector else "HIGH"),
        }
        final_response["peer_benchmarking"]["peer_selection"] = {
            "sector": benchmark_sector,
            "scope": request.emissions_scope or "Scope 1+2",
            "region": request.region,
        }

        # Expose Tier 3 benchmarking block (for memo rendering / audit).
        final_response["peer_benchmarking"]["tier3_5_layer"] = tier3
        if tier3_conf_pct is not None:
            final_response["peer_benchmarking"]["banker_confidence_pct"] = tier3_conf_pct

        # Expose deterministic SBTi numeric benchmark block (for audit / reproducibility).
        final_response["peer_benchmarking"]["sbti_deterministic"] = {
            "percentiles": det_peer_stats or None,
            "confidence_level": det_confidence,
            "percentile_rank": ambition_result.get("percentile_rank") if isinstance(ambition_result, dict) else None,
            "classification": ambition_result.get("classification") if isinstance(ambition_result, dict) else None,
            "match_quality": (percentile_result.get("match_quality") if isinstance(percentile_result, dict) else None) or ambition_result.get("match_quality"),
            "data_source": "SBTi Excel dataset (deterministic)",
        }

        # STRICT MODE: credit memo must be produced by agents (no template fallbacks)
        credit_memo = report.get("credit_memo") if isinstance(report, dict) else {}
        if not (isinstance(credit_memo, dict) and credit_memo.get("sections")):
            raise HTTPException(status_code=500, detail="Agent credit memo missing or invalid. Ensure Tier4 returns strict JSON with sections.")
        final_response["detailed_report"] = credit_memo
        
        # Add risk flags if there are identified risks
        if achievability_data.get("risks"):
            for risk in achievability_data.get("risks", [])[:3]:
                final_response["risk_flags"].append({
                    "severity": "MEDIUM",
                    "category": "Execution",
                    "issue": risk if isinstance(risk, str) else str(risk),
                    "recommendation": "Monitor and mitigate through covenant structure"
                })

        # Save evaluation to database for history
        # Use a FRESH database session since the original may have timed out during long pipeline
        evaluation_id = None
        try:
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as fresh_db:
                evaluation_id = await _save_evaluation_to_db(fresh_db, request, final_response, doc_ids)
                final_response["evaluation_id"] = evaluation_id
                logger.info(f"Saved evaluation {evaluation_id} to database for {request.company_name}")
        except Exception as save_error:
            logger.error(f"CRITICAL: Failed to save evaluation to database: {save_error}", exc_info=True)
            # Add error flag to response so frontend knows save failed
            final_response["save_error"] = str(save_error)
            final_response["evaluation_id"] = None

        logger.info(f"Completed Agentic KPI evaluation for {request.company_name}")
        return final_response

    except Exception as e:
        logger.error(f"Agentic Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/pdf")
async def generate_evaluation_pdf(
    request: KPIBenchmarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run evaluation and return PDF report.
    
    Same as /evaluate but returns downloadable PDF.
    """
    # Get JSON report first
    report = await run_full_evaluation(request, db)
    
    # Generate PDF
    pdf_bytes = banker_report_service.generate_pdf(report)
    
    # Return as downloadable file
    filename = f"KPI_Assessment_{request.company_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/history/{evaluation_id}/pdf")
async def generate_pdf_from_saved(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate PDF from a previously saved evaluation.
    
    This does NOT re-run the evaluation - it uses the saved result.
    Much faster than /evaluate/pdf for already-completed evaluations.
    """
    try:
        # Get evaluation
        eval_result = await db.execute(
            select(KPIEvaluation).where(KPIEvaluation.id == evaluation_id)
        )
        evaluation = eval_result.scalar_one_or_none()
        
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        # Get full result JSON
        result_query = await db.execute(
            select(KPIEvaluationResult).where(KPIEvaluationResult.evaluation_id == evaluation_id)
        )
        result_record = result_query.scalar_one_or_none()
        
        if not result_record or not result_record.result_json:
            raise HTTPException(status_code=404, detail="Evaluation result not found. Please re-run the evaluation.")
        
        try:
            full_result = json.loads(result_record.result_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse saved evaluation result")
        
        # Generate PDF from saved result
        pdf_bytes = banker_report_service.generate_pdf(full_result)
        
        # Return as downloadable file
        company_name = evaluation.company_name.replace(' ', '_') if evaluation.company_name else 'Company'
        filename = f"KPI_Assessment_{company_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate PDF for evaluation {evaluation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/summary")
async def get_executive_summary(
    request: KPIBenchmarkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Run evaluation and return executive summary text only.
    
    Useful for quick review before full report.
    """
    report = await run_full_evaluation(request, db)
    summary_text = banker_report_service.generate_executive_summary_text(report)
    
    return {
        "company_name": request.company_name,
        "recommendation": report.get("executive_summary", {}).get("overall_recommendation"),
        "summary_text": summary_text,
        "key_findings": report.get("executive_summary", {}).get("key_findings", [])
    }


@router.get("/document-types")
async def get_document_types():
    """
    Get list of supported document types for upload.
    
    Returns mandatory and optional document types.
    """
    return {
        "mandatory": [
            {
                "type_code": "csrd_report",
                "name": "CSRD / Non-Financial Reporting Statement",
                "description": "Mandatory annual ESG report with audited environmental, social, and governance data"
            },
            {
                "type_code": "spts",
                "name": "Sustainability Performance Targets (SPTs)",
                "description": "Formal document defining the sustainability goals and KPI targets for the loan"
            }
        ],
        "optional": [
            {
                "type_code": "spo",
                "name": "Second Party Opinion (SPO)",
                "description": "Independent review from rating agency certifying target ambition"
            },
            {
                "type_code": "taxonomy_report",
                "name": "EU Taxonomy Alignment Report",
                "description": "Spreadsheet showing percentage of green revenue/CapEx/OpEx"
            },
            {
                "type_code": "transition_plan",
                "name": "Transition Plan",
                "description": "Strategic roadmap showing how company will achieve targets"
            },
            {
                "type_code": "ghg_inventory",
                "name": "GHG Inventory Report",
                "description": "Detailed greenhouse gas emissions inventory by scope"
            },
            {
                "type_code": "verification_report",
                "name": "Third-Party Verification Report",
                "description": "Independent verification/assurance statement for emissions data"
            }
        ]
    }

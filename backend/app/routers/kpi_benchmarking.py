"""
GreenGuard ESG Platform - KPI Benchmarking Router
Complete API for KPI target assessment, peer benchmarking, and report generation.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kpi-benchmark", tags=["KPI Benchmarking"])


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
    facility_amount: Optional[str] = None
    tenor_years: Optional[int] = None
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
    target_percentage: float = Field(..., description="Target reduction percentage")
    sector: str
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
    target_value: float
    ambition_classification: Optional[str] = None
    margin_adjustment_bps: Optional[int] = None
    use_of_proceeds: Optional[str] = None


# ============================================================
# Endpoints
# ============================================================

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
    Run complete KPI benchmarking evaluation.
    
    This endpoint orchestrates all assessment stages:
    1. KPI extraction from documents
    2. Peer benchmarking and ambition classification
    3. Credibility assessment
    4. ESG risk context (if ticker provided)
    5. Regulatory compliance check
    6. Generate banker-ready report
    
    Args:
        request: Complete evaluation request
    
    Returns:
        Full JSON report (source of truth)
    """
    try:
        logger.info(f"Starting KPI evaluation for {request.company_name}")
        
        # Calculate reduction percentage
        reduction_pct = 0
        if request.baseline_value and request.target_value:
            reduction_pct = round((1 - request.target_value / request.baseline_value) * 100, 1)
        
        # 1. Extract KPIs from primary document if provided
        extraction_data = {}
        primary_doc = next((d for d in request.documents if d.is_primary), None)
        
        # FALLBACK: If no primary doc, use first document
        if not primary_doc and len(request.documents) > 0:
            primary_doc = request.documents[0]
            logger.warning(f"No primary document marked, using document {primary_doc.document_id} as fallback")
        
        if primary_doc:
            logger.info(f"Extracting KPIs from document {primary_doc.document_id}")
            try:
                extraction_result = await kpi_extraction_service.extract_kpis_from_document(
                    primary_doc.document_id
                )
                if extraction_result.get("success"):
                    extraction_data = extraction_result.get("extraction", {})
                    logger.info(f"✓ KPI extraction successful for {request.company_name}")
                else:
                    logger.warning(f"KPI extraction failed: {extraction_result.get('error')}")
            except Exception as extract_error:
                logger.error(f"KPI extraction error: {extract_error}")
                extraction_data = {}
            
            # Extract additional evidence signals for detailed report
            try:
                logger.info(f"Extracting evidence signals from document {primary_doc.document_id}")
                
                # Extract governance signals (board oversight, management incentives)
                governance_result = await kpi_extraction_service.extract_governance_signals(
                    primary_doc.document_id
                )
                if governance_result.get("found"):
                    extraction_data["governance_signals"] = governance_result.get("governance", {})
                
                # Extract verification status (third-party verified, verifier name)
                verification_result = await kpi_extraction_service.extract_verification_status(
                    primary_doc.document_id
                )
                if verification_result.get("found"):
                    extraction_data["verification_status"] = verification_result.get("verification", {})
                
                # Search for past target achievement evidence
                past_targets_result = await kpi_extraction_service.search_for_past_targets(
                    primary_doc.document_id
                )
                if past_targets_result.get("found"):
                    extraction_data["past_performance"] = past_targets_result.get("past_performance", {})
                
                logger.info(f"Evidence extraction complete for {request.company_name}")
            except Exception as evidence_error:
                logger.warning(f"Evidence extraction failed: {evidence_error}")
            
            # =========================================================================
            # CSRD COMPLIANCE & EU TAXONOMY ANALYSIS
            # =========================================================================
            try:
                logger.info(f"🔍 Analyzing CSRD compliance for {request.company_name}")
                csrd_analysis = await csrd_analyzer_service.analyze_csrd_compliance(
                    document_id=primary_doc.document_id,
                    company_name=request.company_name
                )
                extraction_data["csrd_compliance"] = csrd_analysis
                logger.info(f"✓ CSRD compliance score: {csrd_analysis.get('compliance_score', {}).get('overall_score', 'N/A')}")
                
                logger.info(f"🔍 Analyzing EU Taxonomy alignment for {request.company_name}")
                taxonomy_analysis = await taxonomy_service.analyze_taxonomy_alignment(
                    document_id=primary_doc.document_id,
                    company_name=request.company_name,
                    embedding_service=embedding_service
                )
                extraction_data["taxonomy_alignment"] = taxonomy_analysis
                
                if taxonomy_analysis.get("taxonomy_disclosed"):
                    logger.info(f"✓ EU Taxonomy disclosed - Quality: {taxonomy_analysis.get('quality_score', {}).get('quality_level', 'N/A')}")
                else:
                    logger.info("⚠️ No EU Taxonomy disclosure found")
                    
            except Exception as csrd_error:
                logger.error(f"CSRD/Taxonomy analysis error: {csrd_error}")
            # =========================================================================
        
        # 2. INTELLIGENT SECTOR MATCHING - Use AI to research company and match to SBTi sector
        logger.info(f"Researching sector for {request.company_name} (user provided: {request.industry_sector})")
        sector_match = await sector_matching_service.research_company_sector(
            company_name=request.company_name,
            user_provided_industry=request.industry_sector
        )
        
        # Use the matched SBTi sector for peer benchmarking
        matched_sector = sector_match.get("matched_sector", request.industry_sector)
        sector_confidence = sector_match.get("confidence", "LOW")
        logger.info(f"Matched sector: {matched_sector} (confidence: {sector_confidence})")
        
        # 3. Get company target history from SBTi (for trajectory analysis and validation check)
        sbti_target_history = sector_matching_service.get_company_target_history(request.company_name)
        sbti_aligned = sbti_target_history.get("is_sbti_validated", False)
        
        # Also check with legacy method for backward compatibility
        if not sbti_aligned:
            sbti_check = sbti_data_service.check_sbti_commitment(request.company_name)
            sbti_aligned = sbti_check.get("found", False)
        
        logger.info(f"SBTi aligned: {sbti_aligned}, Target history found: {sbti_target_history.get('found')}")
        
        # 4. Get peer data for the matched sector
        peer_data = sector_matching_service.get_peer_targets_for_sector(
            sector=matched_sector,
            scope=request.emissions_scope.replace("Scope ", "")  # Convert "Scope 1+2" to "1+2"
        )
        
        # 5. Peer benchmarking and ambition classification using matched sector
        # CRITICAL: Pass peer_data from sector_matching_service to avoid fallback
        ambition_result = sbti_data_service.classify_ambition(
            borrower_target=reduction_pct,
            sector=matched_sector,  # Use AI-matched sector
            scope=request.emissions_scope,
            sbti_aligned=sbti_aligned,
            region=request.region,
            peer_data=peer_data  # NEW: Pass pre-computed peer data
        )
        
        # Add sector matching info to ambition result
        ambition_result["sector_matching"] = {
            "user_provided_sector": request.industry_sector,
            "matched_sbti_sector": matched_sector,
            "match_confidence": sector_confidence,
            "match_reasoning": sector_match.get("reasoning"),
            "match_source": sector_match.get("source"),
            "researched_industry": sector_match.get("researched_industry")
        }
        
        # Add target history for trajectory analysis (NEW!)
        if sbti_target_history.get("found"):
            ambition_result["sbti_target_history"] = {
                "validated": sbti_target_history.get("is_sbti_validated"),
                "target_count": sbti_target_history.get("target_count"),
                "trajectory": sbti_target_history.get("trajectory_info"),
                "near_term_targets": sbti_target_history.get("near_term_targets", [])[:2],
                "long_term_targets": sbti_target_history.get("long_term_targets", [])[:2]
            }
        
        # Use peer data if available
        if peer_data.get("peer_count", 0) > 0 and "percentiles" in peer_data:
            ambition_result["peer_count"] = peer_data["peer_count"]
            ambition_result["peer_median"] = peer_data["percentiles"]["median"]
            ambition_result["peer_p75"] = peer_data["percentiles"]["p75"]
            ambition_result["confidence_level"] = peer_data["confidence_level"]
        
        # Set baseline verification based on SBTi status AND CSRD assurance (ENHANCED!)
        verification_level = "MODERATE"
        verification_source = "Self-reported"
        verification_rationale = "Baseline from borrower documents"
        
        # Check CSRD data quality for assurance level
        if extraction_data.get("csrd_compliance"):
            data_quality = extraction_data["csrd_compliance"].get("data_quality", {})
            assurance_level = data_quality.get("assurance_level")
            verifier_name = data_quality.get("verifier_name")
            
            if assurance_level == "reasonable":
                verification_level = "HIGH"
                verification_source = f"Reasonable Assurance by {verifier_name or 'Third-party'}"
                verification_rationale = "Baseline verified with reasonable assurance per CSRD requirements"
            elif assurance_level == "limited":
                verification_level = "MEDIUM-HIGH"
                verification_source = f"Limited Assurance by {verifier_name or 'Third-party'}"
                verification_rationale = "Baseline verified with limited assurance (CSRD compliant)"
        
        # SBTi validation overrides to HIGH
        if sbti_aligned:
            verification_level = "HIGH"
            verification_source = "SBTi Database + " + verification_source
            verification_rationale = f"Baseline verified through SBTi validation ({sbti_target_history.get('target_count', 0)} validated targets) and external assurance"
        
        extraction_data["baseline_verification"] = {
            "level": verification_level,
            "source": verification_source,
            "rationale": verification_rationale
        }
        
        logger.info(f"📊 Baseline verification: {verification_level} ({verification_source})")
        
        # 4. Credibility assessment - provide meaningful default when no document
        credibility_result = {
            "credibility_level": "MEDIUM",
            "credibility_rationale": "No supporting documents provided for detailed assessment",
            "signals": {},
            "signal_summary": {
                "detected_count": 0,
                "high_weight_detected": 0,
                "total_possible": 6,
                "missing_signals": ["past_targets_met", "third_party_verified", "board_oversight", 
                                   "management_incentives", "sbti_commitment", "transition_plan"]
            },
            "gaps": [
                {"signal": "Documentation", "recommendation": "Upload CSRD report for detailed credibility assessment"}
            ]
        }
        if primary_doc:
            try:
                credibility_result = await credibility_service.assess_credibility(
                    document_id=primary_doc.document_id,
                    company_name=request.company_name,
                    extraction_data=extraction_data
                )
            except Exception as cred_error:
                logger.warning(f"Credibility assessment failed: {cred_error}")
        
        # 5. ESG risk context - handle API failures gracefully
        esg_scores = None
        if request.ticker:
            try:
                esg_scores = yahoo_esg_service.get_esg_scores(request.ticker)
            except Exception as esg_error:
                logger.warning(f"ESG scores fetch failed: {esg_error}")
                esg_scores = {
                    "available": False,
                    "error": "ESG data temporarily unavailable",
                    "ticker": request.ticker
                }
        
        # 6. Regulatory compliance
        deal_data = {
            "metric": request.metric,
            "target_value": request.target_value,
            "ambition_classification": ambition_result.get("classification"),
            "margin_adjustment_bps": request.margin_adjustment_bps,
            "use_of_proceeds": None  # For green loans
        }
        compliance_result = compliance_checker.check_all_frameworks(
            deal_data=deal_data,
            extraction_data=extraction_data,
            loan_type="sll" if "Sustainability-Linked" in request.loan_type else "green"
        )
        
        # 7. Build evaluation data for report
        evaluation_data = {
            "company_name": request.company_name,
            "ticker": request.ticker,
            "lei": request.lei,
            "loan_type": request.loan_type,
            "facility_amount": request.facility_amount,
            "tenor_years": request.tenor_years,
            "margin_adjustment_bps": request.margin_adjustment_bps,
            "metric": request.metric,
            "target_value": request.target_value,
            "target_unit": request.target_unit,
            "baseline_value": request.baseline_value,
            "baseline_year": request.baseline_year,
            "timeline_end_year": request.timeline_end_year,
            "emissions_scope": request.emissions_scope,
            "document_ids": [d.document_id for d in request.documents]
        }
        
        # 8. Generate AI summaries for the report
        logger.info(f"Generating AI summaries for {request.company_name}")
        try:
            # Generate executive summary narrative
            exec_summary = await ai_summary_service.generate_executive_summary(
                company_name=request.company_name,
                ambition_result=ambition_result,
                credibility_result=credibility_result,
                extraction_data=extraction_data,
                compliance_result=compliance_result,
                recommendation=compliance_result.get("overall_status", "CONDITIONAL_APPROVAL")
            )
            
            # Generate detailed section analyses
            ambition_analysis = await ai_summary_service.generate_ambition_analysis(
                ambition_result=ambition_result,
                sector=matched_sector
            )
            
            credibility_analysis = await ai_summary_service.generate_credibility_analysis(
                credibility_result=credibility_result,
                extraction_data=extraction_data
            )
            
            baseline_analysis = await ai_summary_service.generate_baseline_analysis(
                extraction_data=extraction_data,
                evaluation_data=evaluation_data
            )
            
            # Add AI analyses to extraction data for report generation
            extraction_data["ai_summaries"] = {
                "executive_summary": exec_summary,
                "ambition_analysis": ambition_analysis,
                "credibility_analysis": credibility_analysis,
                "baseline_analysis": baseline_analysis
            }
            logger.info(f"AI summaries generated successfully")
        except Exception as ai_error:
            logger.warning(f"AI summary generation failed: {ai_error}")
            extraction_data["ai_summaries"] = {"error": str(ai_error)}
        
        # 9. Generate full report
        report = banker_report_service.generate_full_report(
            evaluation_data=evaluation_data,
            extraction_data=extraction_data,
            ambition_result=ambition_result,
            credibility_result=credibility_result,
            compliance_result=compliance_result,
            esg_scores=esg_scores
        )
        
        logger.info(f"Completed KPI evaluation for {request.company_name}")
        
        return report
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
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

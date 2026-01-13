from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class BaselineVerificationEnum(str, Enum):
    AUDITED = "audited"
    THIRD_PARTY_VERIFIED = "third_party_verified"
    SELF_REPORTED = "self_reported"
    UNKNOWN = "unknown"

class BankerDecisionEnum(str, Enum):
    PENDING = "PENDING"
    ACCEPT_AS_IS = "ACCEPT_AS_IS"
    NEGOTIATE = "NEGOTIATE"
    REJECT = "REJECT"
    OVERRIDE_AI = "OVERRIDE_AI"

class KPIEvaluationCreate(BaseModel):
    loan_reference_id: str
    company_name: str
    industry_sector: str
    region: str
    metric: str
    target_value: float
    target_unit: str
    timeline_start_year: int
    timeline_end_year: int
    baseline_value: float
    baseline_unit: str = "%"
    baseline_year: int
    baseline_verification: str = "unknown"
    
    # Optional
    company_size_proxy: Optional[str] = None
    emissions_scope: Optional[str] = None
    methodology: Optional[str] = None
    capex_budget: Optional[str] = None
    plan_description: Optional[str] = None
    csrd_reporting_status: Optional[str] = None

class KPIEvaluationDocumentAttach(BaseModel):
    document_ids: List[int]

class KPIEvaluationResponse(BaseModel):
    id: int
    company_name: str
    metric: str
    status: str
    
    # Backwards compatibility / Simple fields
    result_summary: Optional[str] = None
    assessment_grade: Optional[str] = None
    success_probability: Optional[float] = None
    needs_review: bool = False
    
    # Banker Fields
    banker_decision: Optional[str] = "PENDING"
    created_at: datetime

    # Rich Report Fields (Matching Frontend EvaluationResult interface)
    report_header: Optional[Dict[str, Any]] = None
    executive_summary: Optional[Dict[str, Any]] = None
    peer_benchmarking: Optional[Dict[str, Any]] = None
    achievability_assessment: Optional[Dict[str, Any]] = None
    risk_flags: Optional[List[Dict[str, Any]]] = None
    regulatory_compliance: Optional[Dict[str, Any]] = None
    visuals: Optional[Dict[str, Any]] = None # New Visuals Field
    final_decision: Optional[Dict[str, Any]] = None
    detailed_report: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class BankerDecisionCreate(BaseModel):
    decision: BankerDecisionEnum
    override_reason: Optional[str] = None
    accepted_target_value: Optional[float] = None # If negotiated/modified

class EvidenceItem(BaseModel):
    type: str # document, benchmark, peer
    ids: List[str]
    snippet: Optional[str] = None
    confidence: Optional[float] = None

class KPIEvaluationDetailResult(KPIEvaluationResponse):
    inputs: Dict[str, Any]
    comparisons: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None
    evidence: List[EvidenceItem] = []
    audit_trail: List[Dict[str, Any]] = []

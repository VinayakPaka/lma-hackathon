"""
GreenGuard ESG Platform - ESG Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ESGMetrics(BaseModel):
    carbon_emissions: Optional[float] = None
    energy_usage: Optional[float] = None
    renewable_percentage: Optional[float] = None
    water_usage: Optional[float] = None
    waste_recycled: Optional[float] = None


class ESGScores(BaseModel):
    carbon_score: Optional[float] = None
    energy_efficiency_score: Optional[float] = None
    taxonomy_alignment_score: Optional[float] = None
    overall_compliance_score: Optional[float] = None


class ESGExtractionRequest(BaseModel):
    document_id: int


class ESGExtractionResponse(BaseModel):
    report_id: int
    document_id: int
    metrics: ESGMetrics
    scores: ESGScores
    detected_keywords: List[str] = []
    red_flags: List[str] = []
    status: str = "generated"
    generated_at: datetime


class ESGReportResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    metrics: ESGMetrics
    scores: ESGScores
    detected_keywords: List[str] = []
    raw_metrics: Dict[str, Any] = {}
    red_flags: List[str] = []
    recommendations: Optional[str] = None
    report_status: str
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ComplianceScoreResponse(BaseModel):
    report_id: int
    overall_score: float
    carbon_score: float
    energy_efficiency_score: float
    taxonomy_alignment_score: float
    status: str
    breakdown: Dict[str, Any] = {}
    recommendations: List[str] = []

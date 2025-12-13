"""
GreenGuard ESG Platform - KPI and Transaction Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class KPIBenchmarkRequest(BaseModel):
    sector: str
    metric: str


class KPIBenchmarkResponse(BaseModel):
    sector: str
    metric: str
    baseline_range: dict
    market_average: float
    ambitious_target: float
    unit: Optional[str] = None
    recommendation: str


class TransactionVerifyRequest(BaseModel):
    borrower_id: int
    vendor_name: str
    transaction_amount: float = Field(..., gt=0)
    description: Optional[str] = None
    category: Optional[str] = None


class TransactionVerifyResponse(BaseModel):
    transaction_id: int
    borrower_id: int
    vendor_name: str
    amount: float
    is_green_compliant: bool
    verification_status: str
    misuse_risk_score: float
    compliance_notes: Optional[str] = None
    vendor_status: str
    recommendations: List[str] = []


class GreenVendorResponse(BaseModel):
    id: int
    vendor_name: str
    vendor_id: Optional[str] = None
    category: Optional[str] = None
    certification: Optional[str] = None
    is_active: int
    risk_level: str
    
    class Config:
        from_attributes = True

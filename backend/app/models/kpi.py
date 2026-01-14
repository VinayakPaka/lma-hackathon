"""
GreenGuard ESG Platform - KPI and Green Vendor Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, UniqueConstraint
from app.database import Base


class KPIBenchmark(Base):
    """KPI Benchmark database model."""
    __tablename__ = "kpi_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sector = Column(String(100), nullable=False, index=True)
    metric = Column(String(100), nullable=False, index=True)
    target_low = Column(Float, nullable=False)
    target_medium = Column(Float, nullable=False)
    target_high = Column(Float, nullable=False)
    unit = Column(String(50))
    description = Column(String(500))
    source_url = Column(String(500))
    effective_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GreenVendor(Base):
    """Approved green vendor database model."""
    __tablename__ = "green_vendors"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vendor_name = Column(String(255), nullable=False, index=True)
    vendor_id = Column(String(255))
    category = Column(String(100))
    certification = Column(String(255))
    certification_expiry = Column(DateTime)
    is_active = Column(Integer, default=1)
    risk_level = Column(String(20), default="low")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KPIEvaluation(Base):
    """KPI Evaluation request and summary."""
    __tablename__ = "kpi_evaluations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    loan_reference_id = Column(String(100), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    industry_sector = Column(String(100), nullable=False)
    region = Column(String(100), nullable=False)
    metric = Column(String(100), nullable=False)
    target_value = Column(Float, nullable=False)
    target_unit = Column(String(50), nullable=False)
    timeline_start_year = Column(Integer, nullable=False)
    timeline_end_year = Column(Integer, nullable=False)
    baseline_value = Column(Float)
    baseline_unit = Column(String(50))
    baseline_year = Column(Integer)
    baseline_verification = Column(String(50))  # audited, third_party_verified, self_reported, unknown
    
    # Optional context
    company_size_proxy = Column(String(100))
    emissions_scope = Column(String(50))
    methodology = Column(String(255))
    capex_budget = Column(String(100))
    plan_description = Column(Text)
    csrd_reporting_status = Column(String(50))
    
    # Results status
    status = Column(String(50), default="draft", index=True)  # draft, processing, completed, failed
    result_summary = Column(Text)
    assessment_grade = Column(String(20))  # WEAK, MODERATE, AMBITIOUS
    success_probability = Column(Float)
    needs_review = Column(Boolean, default=False)  # PostgreSQL Boolean
    
    # Banker Decision
    banker_decision = Column(String(50), default="PENDING")
    banker_override_reason = Column(Text)
    
    created_by_user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KPIEvaluationDocument(Base):
    """Link between Evaluation and uploaded Documents."""
    __tablename__ = "kpi_evaluation_documents"
    
    evaluation_id = Column(Integer, primary_key=True)
    document_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KPIEvaluationResult(Base):
    """Detailed full JSON result of an evaluation."""
    __tablename__ = "kpi_evaluation_results"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluation_id = Column(Integer, index=True, unique=True, nullable=False)  # One result per evaluation
    result_json = Column(Text, nullable=False)  # Use Text for large JSON (no size limit)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIAuditLog(Base):
    """Audit log for AI operations."""
    __tablename__ = "ai_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluation_id = Column(Integer, index=True)
    action_type = Column(String(50), nullable=False) # EXTRACT, BENCHMARK, SCORE, LLM_GENERATE
    model_provider = Column(String(50))
    input_snapshot = Column(String) # JSON string
    output_snapshot = Column(String) # JSON string
    latency_ms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

"""
GreenGuard ESG Platform - KPI and Green Vendor Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
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

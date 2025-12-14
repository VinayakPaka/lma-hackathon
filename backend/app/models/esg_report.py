"""
GreenGuard ESG Platform - ESG Report Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ESGReport(Base):
    """ESG Report database model."""
    __tablename__ = "esg_reports"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ESG Metrics
    carbon_emissions = Column(Float)
    energy_usage = Column(Float)
    renewable_percentage = Column(Float)
    water_usage = Column(Float)
    waste_recycled = Column(Float)
    
    # Scores
    carbon_score = Column(Float)
    energy_efficiency_score = Column(Float)
    taxonomy_alignment_score = Column(Float)
    overall_compliance_score = Column(Float)
    
    # Analysis data
    detected_keywords = Column(JSON)
    raw_metrics = Column(JSON)
    red_flags = Column(JSON)
    recommendations = Column(JSON)
    
    # Status
    report_status = Column(String(50), default="generated")
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="esg_reports")
    document = relationship("Document", back_populates="esg_reports")
    
    def __repr__(self):
        return f"<ESGReport(id={self.id}, score={self.overall_compliance_score})>"

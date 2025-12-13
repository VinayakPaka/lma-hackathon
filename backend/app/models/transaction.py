"""
GreenGuard ESG Platform - Transaction Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, Text, DateTime, ForeignKey
from app.database import Base


class Transaction(Base):
    """Transaction database model for use-of-proceeds verification."""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    borrower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_id = Column(String(255))
    vendor_name = Column(String(255))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    category = Column(String(100))
    description = Column(Text)
    
    # Compliance fields
    is_green_compliant = Column(Boolean, default=False)
    compliance_notes = Column(Text)
    misuse_risk_score = Column(Float)
    
    # Verification
    verification_status = Column(String(50), default="pending")
    verified_at = Column(DateTime)
    verified_by = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, vendor='{self.vendor_name}', amount={self.amount})>"

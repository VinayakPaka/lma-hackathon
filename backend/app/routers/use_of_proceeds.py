"""
GreenGuard ESG Platform - Use of Proceeds Router
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.kpi_schema import TransactionVerifyRequest, TransactionVerifyResponse
from app.services.vendor_verification import vendor_service
from app.utils.jwt_handler import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/verify", response_model=TransactionVerifyResponse)
async def verify_transaction(
    request: TransactionVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verification = vendor_service.verify_transaction(
        request.vendor_name,
        request.transaction_amount,
        request.description or ""
    )
    
    transaction = Transaction(
        borrower_id=current_user.id,
        vendor_name=request.vendor_name,
        amount=request.transaction_amount,
        category=request.category,
        description=request.description,
        is_green_compliant=verification["is_green_compliant"],
        compliance_notes=verification["compliance_notes"],
        misuse_risk_score=verification["misuse_risk_score"],
        verification_status="verified",
        verified_at=datetime.utcnow()
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    logger.info(f"Transaction verified: {transaction.id}")
    
    return TransactionVerifyResponse(
        transaction_id=transaction.id,
        borrower_id=transaction.borrower_id,
        vendor_name=transaction.vendor_name,
        amount=transaction.amount,
        is_green_compliant=transaction.is_green_compliant,
        verification_status=transaction.verification_status,
        misuse_risk_score=transaction.misuse_risk_score,
        compliance_notes=transaction.compliance_notes,
        vendor_status=verification["vendor_status"],
        recommendations=verification["recommendations"]
    )


@router.get("/transactions")
async def list_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.borrower_id == current_user.id)
        .order_by(Transaction.created_at.desc())
    )
    transactions = result.scalars().all()
    return [
        {
            "id": t.id,
            "vendor_name": t.vendor_name,
            "amount": t.amount,
            "is_green_compliant": t.is_green_compliant,
            "misuse_risk_score": t.misuse_risk_score,
            "created_at": t.created_at.isoformat()
        }
        for t in transactions
    ]


@router.get("/summary")
async def get_verification_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Transaction).where(Transaction.borrower_id == current_user.id)
    )
    transactions = result.scalars().all()
    
    compliant = sum(1 for t in transactions if t.is_green_compliant)
    total_amount = sum(t.amount for t in transactions)
    compliant_amount = sum(t.amount for t in transactions if t.is_green_compliant)
    
    return {
        "total_transactions": len(transactions),
        "compliant_transactions": compliant,
        "non_compliant_transactions": len(transactions) - compliant,
        "total_amount": total_amount,
        "compliant_amount": compliant_amount,
        "compliance_rate": (compliant / len(transactions) * 100) if transactions else 0
    }

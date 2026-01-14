"""GreenGuard ESG Platform - Report Chat Router

Provides report-scoped banker Q&A for KPI evaluation reports.

Endpoints are consumed by the desktop UI:
- POST /report-chat/session
- GET  /report-chat/session/{session_id}
- POST /report-chat/session/{session_id}/message
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.report_chat_schema import (
    ReportChatMessageCreate,
    ReportChatMessageOut,
    ReportChatSessionCreate,
    ReportChatSessionHistoryOut,
    ReportChatSessionOut,
    ReportChatCitation,
)
from app.services.report_chat_service import report_chat_service
from app.utils.jwt_handler import get_current_user

router = APIRouter(prefix="/report-chat", tags=["Report Chat"])
logger = logging.getLogger(__name__)


def _parse_citations(citations_json: Optional[str]) -> List[ReportChatCitation]:
    if not citations_json:
        return []
    try:
        data = json.loads(citations_json)
        if not isinstance(data, list):
            return []
        out: List[ReportChatCitation] = []
        for c in data:
            if not isinstance(c, dict):
                continue
            out.append(
                ReportChatCitation(
                    type=str(c.get("type") or "report"),
                    reference=str(c.get("reference") or ""),
                    snippet=c.get("snippet"),
                    meta=c.get("meta") if isinstance(c.get("meta"), dict) else None,
                )
            )
        return out
    except Exception:
        return []


@router.post("/session", response_model=ReportChatSessionOut)
async def create_or_get_session(
    request: ReportChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session = await report_chat_service.create_or_get_session(
            db,
            evaluation_id=request.evaluation_id,
            user_id=current_user.id,
            title=request.title,
        )
        return ReportChatSessionOut(
            id=session.id,
            evaluation_id=session.evaluation_id,
            title=session.title,
            created_at=session.created_at,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            logger.error(f"ReportChat 404: {msg} for eval_id={request.evaluation_id} user_id={current_user.id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        logger.exception("Failed to create/get report chat session")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/session/{session_id}", response_model=ReportChatSessionHistoryOut)
async def get_session_history(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        session, messages = await report_chat_service.get_session_history(
            db,
            session_id=session_id,
            user_id=current_user.id,
        )

        return ReportChatSessionHistoryOut(
            session=ReportChatSessionOut(
                id=session.id,
                evaluation_id=session.evaluation_id,
                title=session.title,
                created_at=session.created_at,
            ),
            messages=[
                ReportChatMessageOut(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at,
                    citations=_parse_citations(m.citations_json),
                )
                for m in messages
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception("Failed to load report chat history")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/session/{session_id}/message", response_model=ReportChatMessageOut)
async def send_message(
    session_id: int,
    request: ReportChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not request.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    try:
        msg = await report_chat_service.send_message(
            db,
            session_id=session_id,
            user_id=current_user.id,
            message=request.message,
        )

        return ReportChatMessageOut(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            citations=_parse_citations(msg.citations_json),
        )
    except ValueError as e:
        msg = str(e)
        if "perplexity_api_key" in msg.lower() or "ai" in msg.lower() and "configured" in msg.lower():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    except Exception as e:
        logger.exception("Failed to send report chat message")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

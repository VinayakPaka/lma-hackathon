from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportChatSessionCreate(BaseModel):
    evaluation_id: int = Field(..., ge=1)
    title: Optional[str] = None


class ReportChatSessionOut(BaseModel):
    id: int
    evaluation_id: int
    title: Optional[str] = None
    created_at: datetime


class ReportChatMessageCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class ReportChatCitation(BaseModel):
    type: str
    reference: str
    snippet: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ReportChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    citations: List[ReportChatCitation] = []


class ReportChatSessionHistoryOut(BaseModel):
    session: ReportChatSessionOut
    messages: List[ReportChatMessageOut]

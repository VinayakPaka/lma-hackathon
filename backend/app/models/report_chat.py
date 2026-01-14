"""GreenGuard ESG Platform - Report Chat Models

Chat sessions and messages scoped to a KPI evaluation report.

LLM is used only to explain/summarize based on provided evidence.
Deterministic scoring/approval logic remains unchanged.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ReportChatSession(Base):
    """A chat session bound to a KPI evaluation (report)."""

    __tablename__ = "report_chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluation_id = Column(
        Integer,
        ForeignKey("kpi_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "ReportChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ReportChatMessage.created_at.asc()",
    )


class ReportChatMessage(Base):
    """A single message in a report chat session."""

    __tablename__ = "report_chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("report_chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(String(20), nullable=False)  # system|user|assistant
    content = Column(Text, nullable=False)

    # JSON string (list of citations) for audit + UI.
    citations_json = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ReportChatSession", back_populates="messages")

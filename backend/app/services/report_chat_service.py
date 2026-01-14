"""GreenGuard ESG Platform - Report Chat Service

Implements report-scoped banker Q&A using:
- RAG over borrower document embeddings (Supabase pgvector via embedding_service)
- Stored report JSON (KPIEvaluationResult.result_json)
- Perplexity chat completions for natural language responses

Chat history is persisted in DB for auditability.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.kpi import KPIEvaluation, KPIEvaluationDocument, KPIEvaluationResult
from app.models.report_chat import ReportChatSession, ReportChatMessage
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are GreenGuard's banker-facing Q&A assistant.

You answer questions ONLY using:
1) the saved evaluation report JSON (this is the generated report), and
2) the uploaded borrower documents retrieved via RAG.

Hard rules:
- Never invent facts. If evidence is missing, say you don't know.
- Never change or recompute scores/percentiles/decisions.
- When explaining "why", point to the report fields and the evidence excerpts.
- Prefer concise, audit-friendly language.

Return your response as JSON ONLY in this schema:
{
  "answer": "string",
  "citations": [
    {"type": "report"|"document", "reference": "string", "snippet": "string", "meta": {}}
  ]
}
"""


class ReportChatService:
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def create_or_get_session(
        self,
        db: AsyncSession,
        *,
        evaluation_id: int,
        user_id: int,
        title: Optional[str] = None,
    ) -> ReportChatSession:
        # Check if evaluation exists (any user can access if they can view it in history)
        eval_res = await db.execute(
            select(KPIEvaluation).where(
                KPIEvaluation.id == evaluation_id,
            )
        )
        if not eval_res.scalar_one_or_none():
            raise ValueError("Evaluation not found")

        result = await db.execute(
            select(ReportChatSession).where(
                ReportChatSession.evaluation_id == evaluation_id,
                ReportChatSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()
        if session:
            if title and (not session.title):
                session.title = title
                await db.commit()
                await db.refresh(session)
            return session

        session = ReportChatSession(evaluation_id=evaluation_id, user_id=user_id, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session_history(
        self,
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        limit: int = 100,
    ) -> Tuple[ReportChatSession, List[ReportChatMessage]]:
        res = await db.execute(
            select(ReportChatSession).where(
                ReportChatSession.id == session_id,
                ReportChatSession.user_id == user_id,
            )
        )
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError("Chat session not found")

        msg_res = await db.execute(
            select(ReportChatMessage)
            .where(ReportChatMessage.session_id == session_id)
            .order_by(ReportChatMessage.created_at.asc())
            .limit(limit)
        )
        messages = list(msg_res.scalars().all())
        return session, messages

    async def send_message(
        self,
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        message: str,
    ) -> ReportChatMessage:
        # Validate session ownership
        session_res = await db.execute(
            select(ReportChatSession).where(
                ReportChatSession.id == session_id,
                ReportChatSession.user_id == user_id,
            )
        )
        session = session_res.scalar_one_or_none()
        if not session:
            raise ValueError("Chat session not found")

        # Ensure evaluation exists (user has already validated access via session)
        eval_res = await db.execute(
            select(KPIEvaluation).where(
                KPIEvaluation.id == session.evaluation_id,
            )
        )
        evaluation = eval_res.scalar_one_or_none()
        if not evaluation:
            raise ValueError("Evaluation not found")

        # Persist user message
        user_msg = ReportChatMessage(session_id=session.id, role="user", content=message)
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)

        # Build context (report JSON + RAG chunks)
        report_json_text = await self._load_report_json(db, evaluation_id=session.evaluation_id)
        doc_ids = await self._load_evaluation_document_ids(db, evaluation_id=session.evaluation_id)

        rag_chunks, rag_citations = await self._retrieve_rag_context(doc_ids, message)

        # Add lightweight conversational memory (last 12 messages excluding system)
        _, history = await self.get_session_history(db, session_id=session.id, user_id=user_id, limit=30)
        chat_memory = history[:-1][-12:]  # exclude the most recent user message

        prompt = self._build_user_prompt(
            question=message,
            report_json_text=report_json_text,
            rag_chunks_text=rag_chunks,
        )

        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Append short conversation context (without citations) to improve continuity.
        for m in chat_memory:
            if m.role not in ("user", "assistant"):
                continue
            messages_payload.append({"role": m.role, "content": m.content[:4000]})
        messages_payload.append({"role": "user", "content": prompt})

        llm_answer, llm_citations = await self._ask_perplexity(messages_payload)

        citations = self._merge_citations(rag_citations, llm_citations)
        citations_json = json.dumps(citations, ensure_ascii=False)

        assistant_msg = ReportChatMessage(
            session_id=session.id,
            role="assistant",
            content=llm_answer,
            citations_json=citations_json,
        )
        db.add(assistant_msg)
        await db.commit()
        await db.refresh(assistant_msg)
        return assistant_msg

    async def _load_report_json(self, db: AsyncSession, *, evaluation_id: int) -> str:
        res = await db.execute(
            select(KPIEvaluationResult).where(KPIEvaluationResult.evaluation_id == evaluation_id)
        )
        rec = res.scalar_one_or_none()
        if not rec or not rec.result_json:
            return "{}"
        # Keep context bounded.
        text = rec.result_json
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, ensure_ascii=False, indent=2)[:45000]
        except Exception:
            return text[:45000]

    async def _load_evaluation_document_ids(self, db: AsyncSession, *, evaluation_id: int) -> List[int]:
        res = await db.execute(
            select(KPIEvaluationDocument.document_id).where(
                KPIEvaluationDocument.evaluation_id == evaluation_id
            )
        )
        return [int(x) for x in res.scalars().all()]

    async def _retrieve_rag_context(
        self, doc_ids: List[int], question: str
    ) -> Tuple[str, List[Dict[str, Any]]]:
        if not doc_ids:
            return "", []

        chunks: List[str] = []
        citations: List[Dict[str, Any]] = []

        # Pull a small number per doc so we don't blow context window.
        per_doc_k = 4

        for doc_id in doc_ids[:10]:
            try:
                results = embedding_service.search_similar(
                    query=question,
                    document_id=doc_id,
                    top_k=per_doc_k,
                )
            except Exception as e:
                logger.warning(f"RAG retrieval failed for doc {doc_id}: {e}")
                continue

            for r in (results or []):
                content = (r.get("content") or "").strip()
                if not content:
                    continue
                meta = r.get("metadata") or {}
                page = meta.get("page") or meta.get("page_number")
                ref = f"document_id={doc_id}" + (f", page={page}" if page is not None else "")
                snippet = content[:240]

                chunks.append(f"[Doc {doc_id}{' Page ' + str(page) if page is not None else ''}]\n{content}")
                citations.append(
                    {
                        "type": "document",
                        "reference": ref,
                        "snippet": snippet,
                        "meta": {
                            "document_id": doc_id,
                            "page": page,
                            "chunk_index": r.get("chunk_index"),
                            "score": r.get("similarity") or r.get("score"),
                        },
                    }
                )

        # Deduplicate chunks by leading snippet
        seen = set()
        deduped_chunks: List[str] = []
        for c in chunks:
            key = c[:180]
            if key in seen:
                continue
            seen.add(key)
            deduped_chunks.append(c)

        return "\n\n---\n\n".join(deduped_chunks)[:45000], citations[:20]

    def _build_user_prompt(self, *, question: str, report_json_text: str, rag_chunks_text: str) -> str:
        return (
            "You are answering a banker question about a generated KPI assessment report.\n\n"
            "BANKER QUESTION:\n"
            f"{question}\n\n"
            "REPORT JSON (source-of-truth):\n"
            f"{report_json_text}\n\n"
            "RETRIEVED DOCUMENT EXCERPTS (RAG):\n"
            f"{rag_chunks_text or '[no document excerpts retrieved]'}\n\n"
            "Instructions:\n"
            "- Use only the provided REPORT JSON and DOCUMENT EXCERPTS.\n"
            "- If the question is about 'why', cite which report fields drove that statement.\n"
            "- If you cannot find support, say so explicitly.\n"
        )

    async def _ask_perplexity(self, messages: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, Any]]]:
        if not settings.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY is not configured")

        payload = {
            "model": settings.PERPLEXITY_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 900,
        }
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }

        resp = await self.http_client.post(settings.PERPLEXITY_API_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

        parsed = self._parse_json_response(content)
        if isinstance(parsed, dict) and isinstance(parsed.get("answer"), str):
            answer = parsed.get("answer")
            citations = parsed.get("citations") if isinstance(parsed.get("citations"), list) else []
            normalized = []
            for c in citations:
                if not isinstance(c, dict):
                    continue
                normalized.append(
                    {
                        "type": c.get("type") or "report",
                        "reference": c.get("reference") or "",
                        "snippet": c.get("snippet"),
                        "meta": c.get("meta") if isinstance(c.get("meta"), dict) else {},
                    }
                )
            return answer, normalized

        # Fallback: treat raw text as answer
        return content.strip(), []

    def _parse_json_response(self, response: str) -> Any:
        if not response:
            return None

        text = response.strip()
        if text.startswith("```"):
            # Strip fenced block
            text = text.strip("`")
            # remove optional language tag
            if "\n" in text:
                text = text.split("\n", 1)[1]
        text = text.strip()

        # Attempt to locate JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
        else:
            candidate = text

        try:
            return json.loads(candidate)
        except Exception:
            return None

    def _merge_citations(
        self, rag_citations: List[Dict[str, Any]], llm_citations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        # Start with RAG citations (always evidence-backed)
        merged: List[Dict[str, Any]] = []
        seen = set()

        def add(c: Dict[str, Any]):
            key = (c.get("type"), c.get("reference"), (c.get("snippet") or "")[:60])
            if key in seen:
                return
            seen.add(key)
            merged.append(c)

        for c in rag_citations[:12]:
            add(c)
        for c in llm_citations[:12]:
            add(c)

        return merged


report_chat_service = ReportChatService()

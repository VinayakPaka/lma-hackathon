"""
GreenGuard ESG Platform - KPI Evaluation Service
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.kpi import KPIEvaluation, KPIEvaluationDocument, KPIEvaluationResult, AIAuditLog
from app.schemas.kpi_evaluation_schema import (
    KPIEvaluationCreate, 
    KPIEvaluationResponse, 
    BankerDecisionEnum,
    KPIEvaluationDetailResult
)
from app.services.embedding_service import embedding_service
from app.services.ai_esg_service import ai_esg_service
from app.config import settings

logger = logging.getLogger(__name__)

class KPIEvaluationService:
    """Service for Banker KPI Benchmarking and Target Verification."""

    async def create_evaluation(self, db: AsyncSession, request: KPIEvaluationCreate, user_id: int) -> KPIEvaluation:
        """Create a new evaluation request."""
        db_evaluation = KPIEvaluation(
            **request.model_dump(),
            status="draft",
            created_by_user_id=user_id
        )
        db.add(db_evaluation)
        await db.commit()
        await db.refresh(db_evaluation)
        return db_evaluation

    async def get_evaluation(self, db: AsyncSession, evaluation_id: int) -> Optional[KPIEvaluation]:
        """Get evaluation by ID."""
        result = await db.execute(select(KPIEvaluation).filter(KPIEvaluation.id == evaluation_id))
        return result.scalars().first()

    async def list_evaluations(self, db: AsyncSession, user_id: int) -> List[KPIEvaluation]:
        """List evaluations for a user."""
        result = await db.execute(
            select(KPIEvaluation)
            .filter(KPIEvaluation.created_by_user_id == user_id)
            .order_by(KPIEvaluation.created_at.desc())
        )
        return result.scalars().all()

    async def attach_documents(self, db: AsyncSession, evaluation_id: int, document_ids: List[int]):
        """Attach documents to an evaluation."""
        for doc_id in document_ids:
            link = KPIEvaluationDocument(evaluation_id=evaluation_id, document_id=doc_id)
            db.add(link)
        await db.commit()

    async def run_verification(self, db: AsyncSession, evaluation_id: int) -> KPIEvaluation:
        """
        Run the full verification pipeline:
        1. Input Validation
        2. Evidence Extraction (RAG from docs)
        3. Benchmark Lookup (Web Search via Perplexity)
        4. Scoring
        5. Narrative Generation
        """
        evaluation = await self.get_evaluation(db, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")

        evaluation.status = "processing"
        await db.commit()

        try:
            # Check if AI is configured before attempting analysis
            if not settings.PERPLEXITY_API_KEY:
                error_msg = "PERPLEXITY_API_KEY is not configured. AI analysis cannot be performed."
                logger.error(error_msg)
                raise HTTPException(
                    status_code=503,
                    detail=error_msg + " Please configure API keys in your .env file."
                )
            
            # Try AI-powered analysis with timeout
            import asyncio
            
            try:
                # Set a 60-second timeout for the entire AI pipeline (increased from 30s)
                analysis_result = await asyncio.wait_for(
                    self._run_ai_analysis(db, evaluation),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                logger.error(f"AI analysis timed out for evaluation {evaluation_id} after 60 seconds")
                raise HTTPException(
                    status_code=504,
                    detail="AI analysis timed out. Please try again or reduce document size."
                )
            except Exception as e:
                logger.error(f"AI analysis failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"AI analysis failed: {str(e)}"
                )
            
            # Update Evaluation
            evaluation.status = "completed"
            evaluation.assessment_grade = analysis_result.get("assessment_grade", "MODERATE")
            evaluation.success_probability = analysis_result.get("success_probability", 0.5)
            evaluation.result_summary = analysis_result.get("summary", "")
            evaluation.needs_review = analysis_result.get("needs_review", False)
            
            # Save detailed result
            result_record = KPIEvaluationResult(
                evaluation_id=evaluation.id,
                result_json=json.dumps(analysis_result)
            )
            db.add(result_record)
            
            await db.commit()
            await db.refresh(evaluation)
            return evaluation

        except Exception as e:
            logger.error(f"Error in verification pipeline: {str(e)}")
            evaluation.status = "failed"
            evaluation.result_summary = f"Error: {str(e)}"
            await db.commit()
            raise

    async def _run_ai_analysis(self, db: AsyncSession, evaluation: KPIEvaluation) -> Dict[str, Any]:
        """Run AI-powered analysis (may timeout)."""
        # 1. Gather Context & Evidence
        evidence = await self._gather_evidence(db, evaluation)
        
        # 2. Web Search for Benchmarks
        benchmark_data = await self._search_benchmarks(evaluation)
        
        # 3. Analyze & Score
        analysis_result = await self._analyze_and_score(evaluation, evidence, benchmark_data)
        return analysis_result

    def _fallback_analysis(self, evaluation: KPIEvaluation) -> Dict[str, Any]:
        """
        Provide fallback analysis when AI is unavailable using static benchmarks.
        NOTE: This method should not be used in production. It's only for development/testing.
        """
        logger.warning("Using fallback analysis - this should not happen in production!")
        logger.warning("Please ensure PERPLEXITY_API_KEY is configured in your .env file")
        
        # Use static benchmarks from kpi_service
        from app.services.kpi_service import KPI_BENCHMARKS
        
        sector = evaluation.industry_sector
        metric = evaluation.metric
        target = evaluation.target_value
        
        # Get benchmark data if available
        benchmark = KPI_BENCHMARKS.get(sector, {}).get(metric, {})
        
        if benchmark:
            avg = benchmark.get("avg", 20)
            target_ambitious = benchmark.get("target", 40)
            
            # Simple scoring logic
            if target >= target_ambitious:
                grade = "AMBITIOUS"
                probability = 0.6
            elif target >= avg:
                grade = "MODERATE"
                probability = 0.75
            else:
                grade = "WEAK"
                probability = 0.9
            
            summary = f"⚠️ FALLBACK MODE: Target of {target}% {metric.replace('_', ' ')} compared to industry average of {avg}% and ambitious target of {target_ambitious}%."
        else:
            # No benchmark data available
            grade = "MODERATE"
            probability = 0.5
            summary = f"⚠️ FALLBACK MODE: Limited benchmark data available for {sector}/{metric}. Manual review required."
        
        return {
            "assessment_grade": grade,
            "success_probability": probability,
            "summary": summary,
            "needs_review": True,
            "recommended_target": benchmark.get("target") if benchmark else None,
            "rationale": "⚠️ WARNING: Analysis performed using static benchmarks (AI not configured). Configure PERPLEXITY_API_KEY for accurate analysis.",
            "evidence": [],
            "fallback_mode": True
        }

    async def submit_decision(self, db: AsyncSession, evaluation_id: int, decision: str, reason: Optional[str] = None):
        """Submit banker decision."""
        evaluation = await self.get_evaluation(db, evaluation_id)
        if not evaluation:
            raise HTTPException(status_code=404, detail="Evaluation not found")
        
        evaluation.banker_decision = decision
        evaluation.banker_override_reason = reason
        await db.commit()
        await db.refresh(evaluation)
        return evaluation

    # --- Private Helpers ---

    async def _gather_evidence(self, db: AsyncSession, evaluation: KPIEvaluation) -> Dict[str, Any]:
        """Extract evidence from attached documents using RAG."""
        # Get attached document IDs
        result = await db.execute(
            select(KPIEvaluationDocument.document_id).filter(KPIEvaluationDocument.evaluation_id == evaluation.id)
        )
        doc_ids = result.scalars().all()
        
        evidence_text = ""
        evidence_sources = []

        for doc_id in doc_ids:
            # Search for relevant chunks for this specific metric
            query = f"baseline {evaluation.metric} target {evaluation.target_value} {evaluation.target_unit} {evaluation.timeline_start_year}"
            chunks = embedding_service.search_similar(query, document_id=doc_id, top_k=3)
            
            for chunk in chunks:
                evidence_text += chunk["content"] + "\n---\n"
                evidence_sources.append({
                    "type": "document",
                    "id": str(doc_id),
                    "chunk_id": chunk.get("id"),
                    "snippet": chunk["content"][:100] + "..."
                })
        
        return {"text": evidence_text, "sources": evidence_sources}

    async def _search_benchmarks(self, evaluation: KPIEvaluation) -> Dict[str, Any]:
        """Search the web via Perplexity for industry benchmarks."""
        
        query = (
            f"What are the industry standard benchmarks for {evaluation.metric} in the {evaluation.industry_sector} sector "
            f"for {evaluation.region}? Return average, best-in-class, and weak targets. "
            f"Focus on {evaluation.baseline_year} to {evaluation.timeline_end_year} timeline."
        )
        
        messages = [
            {"role": "system", "content": "You are a specialized ESG research assistant. Find specific numeric benchmarks."},
            {"role": "user", "content": query}
        ]
        
        # We reuse the helper from ai_esg_service to call Perplexity
        # Note: In a real app we might want to decouple this more, but for hackathon this is efficient.
        try:
            response_text = await ai_esg_service._call_perplexity(messages, temperature=0.1)
            # In a real implementation we would parse this more strictly
            return {"raw_text": response_text, "source": "perplexity_web_search"}
        except Exception as e:
            logger.error(f"Benchmark search failed: {e}")
            return {"raw_text": "Benchmark search failed.", "source": "error"}

    async def _analyze_and_score(self, evaluation: KPIEvaluation, evidence: Dict[str, Any], benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to synthesize inputs, evidence, and benchmarks into a final score and narrative.
        """
        
        # Construct a detailed prompt for the LLM
        prompt = f"""
        Act as a strict sustainable finance credit officer. Evaluate this customized KPI target.
        
        CONTEXT:
        Company: {evaluation.company_name} ({evaluation.industry_sector}, {evaluation.region})
        Proposed Target: {evaluation.metric} of {evaluation.target_value} {evaluation.target_unit} by {evaluation.timeline_end_year} (Base: {evaluation.baseline_year})
        
        EVIDENCE FROM DOCS:
        {evidence.get('text', 'No document evidence provided.')}
        
        INDUSTRY BENCHMARKS (Web Search):
        {benchmark_data.get('raw_text', 'No benchmark data found.')}
        
        TASK:
        1. Classify the target as WEAK, MODERATE, or AMBITIOUS.
        2. Estimate success probability (0.0 to 1.0).
        3. Provide a summary rationale.
        4. Recommend a counter-target if weak.
        
        OUTPUT JSON ONLY:
        {{
            "assessment_grade": "WEAK|MODERATE|AMBITIOUS",
            "success_probability": 0.0-1.0,
            "summary": "...",
            "needs_review": boolean,
            "recommended_target": "...",
            "rationale": "..."
        }}
        """
        
        messages = [
            {"role": "system", "content": "You are a JSON-only API. Output must be valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        response_text = await ai_esg_service._call_perplexity(messages, temperature=0.2)
        
        try:
            result = ai_esg_service._parse_json_response(response_text)
            # Merge evidence sources into result for frontend
            result["evidence"] = evidence.get("sources", [])
            return result
        except Exception as e:
            logger.error(f"Scoring parsing failed: {e}")
            # Fallback
            return {
                "assessment_grade": "MODERATE",
                "success_probability": 0.5,
                "summary": "Automatic scoring failed. Please review manually.",
                "needs_review": True
            }

kpi_evaluation_service = KPIEvaluationService()

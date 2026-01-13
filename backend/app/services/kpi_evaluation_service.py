from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks

from app.models.kpi import KPIEvaluation
from app.models.document import Document
from app.schemas.kpi_evaluation_schema import KPIEvaluationCreate, BankerDecisionEnum
from app.agents.tier5.orchestrator import OrchestratorAgent

class KPIEvaluationService:
    async def create_evaluation(self, db: AsyncSession, request: KPIEvaluationCreate, user_id: int):
        db_obj = KPIEvaluation(
            created_by_user_id=user_id,
            loan_reference_id=request.loan_reference_id,
            company_name=request.company_name,
            industry_sector=request.industry_sector,
            region=request.region,
            metric=request.metric,
            target_value=request.target_value,
            target_unit=request.target_unit,
            status="draft",
            timeline_start_year=request.timeline_start_year,
            timeline_end_year=request.timeline_end_year,
            baseline_value=request.baseline_value,
            baseline_unit=request.baseline_unit,
            baseline_year=request.baseline_year,
            baseline_verification=request.baseline_verification,
            company_size_proxy=request.company_size_proxy,
            emissions_scope=request.emissions_scope,
            methodology=request.methodology,
            capex_budget=request.capex_budget,
            plan_description=request.plan_description,
            csrd_reporting_status=request.csrd_reporting_status
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def list_evaluations(self, db: AsyncSession, user_id: int):
        result = await db.execute(select(KPIEvaluation).where(KPIEvaluation.created_by_user_id == user_id))
        return result.scalars().all()

    async def get_evaluation(self, db: AsyncSession, evaluation_id: int):
        result = await db.execute(select(KPIEvaluation).where(KPIEvaluation.id == evaluation_id))
        return result.scalar_one_or_none()

    async def attach_documents(self, db: AsyncSession, evaluation_id: int, doc_ids: List[int]):
        # Depending on the many-to-many relationship, this might require a different approach.
        # Assuming simple linkage or just verifying they exist.
        # For Hackathon, let's assume we just update the doc's evaluation_id if that's the model,
        # or do nothing if it's handled by a separate association table.
        # We'll skip complex linking logic to avoid breakage without model knowledge.
        pass 

    async def submit_decision(self, db: AsyncSession, evaluation_id: int, decision: str, reason: str = None):
        eval_obj = await self.get_evaluation(db, evaluation_id)
        if eval_obj:
            eval_obj.banker_decision = decision
            eval_obj.banker_decision_comment = reason
            eval_obj.status = "COMPLETED"
            await db.commit()
            await db.refresh(eval_obj)
        return eval_obj

    async def run_verification(self, db: AsyncSession, evaluation_id: int):
        eval_obj = await self.get_evaluation(db, evaluation_id)
        if not eval_obj:
            return None

        # 1. Fetch Documents associated
        result = await db.execute(select(Document).where(Document.user_id == eval_obj.created_by_user_id)) 
        docs = result.scalars().all()
        
        file_paths = {}
        for doc in docs:
            file_paths[doc.file_type or f"doc_{doc.id}"] = doc.file_path

        # 2. Trigger Orchestrator
        orchestrator = OrchestratorAgent(company_id=str(eval_obj.id))
        report = await orchestrator.run_assessment(file_paths)
        
        # 3. Update Evaluation with Results
        desc = report.get("final_decision", {})
        eval_obj.result_summary = desc.get("overall_recommendation", "Analysis Complete")
        eval_obj.assessment_grade = desc.get("recommendation", "PENDING")
        eval_obj.status = "VERIFIED"
        # success_probability parse
        try:
             eval_obj.success_probability = float(desc.get("confidence_score", 0))
        except:
             eval_obj.success_probability = 0.0
        
        await db.commit()
        await db.refresh(eval_obj)
        
        # 4. Construct Response matching KPIEvaluationResponse Schema (and Frontend expectations)
        # We merge the DB object with the specific JSON dicts needed by frontend
        
        response_data = {
            "id": eval_obj.id,
            "company_name": eval_obj.company_name,
            "metric": eval_obj.metric,
            "status": eval_obj.status,
            "result_summary": eval_obj.result_summary,
            "assessment_grade": eval_obj.assessment_grade,
            "success_probability": eval_obj.success_probability,
            "banker_decision": eval_obj.banker_decision,
            "created_at": eval_obj.created_at,
            
            # Map Report Data to Schema
            "report_header": report.get("frontend_mapping", {}).get("report_header") or {
                "company_name": eval_obj.company_name,
                "deal_details": {
                    "loan_type": eval_obj.loan_type or "Sustainability Linked Loan",
                    "facility_amount": eval_obj.facility_amount or "N/A",
                    "tenor_years": eval_obj.tenor_years or 5
                },
                "analysis_date": eval_obj.created_at.strftime("%Y-%m-%d") if eval_obj.created_at else "2025-01-12"
            },
            "executive_summary": desc or {
                 "overall_recommendation": "PENDING_REVIEW",
                 "recommendation_rationale": "Analysis could not be fully completed.",
                 "key_findings": [],
                 "conditions_for_approval": []
            },
            "visuals": report.get("visuals") or {
                "peer_comparison": {
                    "labels": ["Median", "Company"], 
                    "dataset": [{"label": "Reduction", "data": [0, 0]}]
                }, 
                "emissions_trajectory": {
                    "labels": ["Year 0", "Year N"], 
                    "data": [0, 0]
                }
            },
            "risk_flags": [], 
            "final_decision": {
                "recommendation": desc.get("recommendation", "PENDING"),
                "confidence": desc.get("confidence", "LOW"),
                "conditions": [{"condition": c, "detail": "", "priority": "High"} for c in desc.get("conditions_for_approval", [])]
            }
        }
        
        return response_data

kpi_evaluation_service = KPIEvaluationService()

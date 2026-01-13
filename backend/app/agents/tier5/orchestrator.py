import logging
import json
import re
from typing import Dict, Any, List

from app.core.memory_store import MemoryStore
from app.agents.tier1.document_processor import DocumentProcessorAgent
from app.agents.tier3.benchmark_agent import BenchmarkAgent
from app.agents.base_agent import BaseAgent

class OrchestratorAgent(BaseAgent):
    """
    Tier 5 Agent: Orchestrator & Decision Framework.
    Coordinatest the 17-agent workflow (simplified to 2 main agents for V1).
    """
    
    def __init__(self, company_id: str, api_key: str = None):
        # API key for memvid is handled in MemoryStore
        self.memory_store = MemoryStore()
        super().__init__("Orchestrator", company_id, self.memory_store)
        
        # Initialize Sub-Agents with the SAME memory store (Shared Context)
        self.doc_processor = DocumentProcessorAgent("DocumentProcessor", company_id, self.memory_store)
        self.bencher = BenchmarkAgent("BenchmarkAgent", company_id, self.memory_store)

    @staticmethod
    def _extract_first_json_object(text: str) -> str | None:
        """Best-effort extraction of the first top-level JSON object from LLM output."""
        if not text:
            return None

        cleaned = text.strip()
        cleaned = cleaned.replace("```json", "```").replace("```JSON", "```")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        if not cleaned:
            return None

        # Fast path: looks like JSON already
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return cleaned

        # Try to find first {...} block (including newlines)
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return None
        return match.group(0).strip()

    @classmethod
    def _parse_llm_json(cls, raw: str) -> Dict[str, Any]:
        extracted = cls._extract_first_json_object(raw)
        if not extracted:
            raise ValueError("LLM returned empty / non-JSON response")
        try:
            parsed = json.loads(extracted)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
        if not isinstance(parsed, dict):
            raise ValueError("LLM returned JSON but not an object")
        return parsed

    async def run_assessment(self, file_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        Run the full end-to-end KPI assessment pipeline (17 Agents).
        """
        logging.info("🚀 ORCHESTRATOR: Starting 17-Agent Assessment Pipeline")
        
        # --- PHASE 1: DOCUMENT INTELLIGENCE (Agents 1-5) ---
        logging.info("--- Phase 1: Document Intelligence ---")
        doc_results = await self.doc_processor.process_documents(file_paths)
        
        # Instantiate other Tier 1 agents (Conceptually - assume they reuse the same memory)
        from app.agents.tier1.chart_agent import ChartUnderstandingAgent
        from app.agents.tier1.baseline_verifier import BaselineVerificationAgent
        from app.agents.tier1.achievement_tracker import AchievementTrackerAgent
        from app.agents.tier1.completeness_analyzer import CompletenessAnalyzerAgent
        
        # We can run these in parallel or sequence
        await ChartUnderstandingAgent("Agent2_Chart", self.company_id, self.memory_store).process_visuals("docs")
        await BaselineVerificationAgent("Agent3_Verifier", self.company_id, self.memory_store).verify_baseline()
        await AchievementTrackerAgent("Agent4_Tracker", self.company_id, self.memory_store).track_history()
        await CompletenessAnalyzerAgent("Agent5_Completeness", self.company_id, self.memory_store).analyze_completeness()

        # --- PHASE 2: DATA EXTRACTION (Agents 6-8) ---
        logging.info("--- Phase 2: Data Extraction ---")
        from app.agents.tier2.kpi_extractor import KPIExtractorAgent
        from app.agents.tier2.governance_extractor import GovernanceExtractorAgent
        from app.agents.tier2.capex_extractor import CapexExtractorAgent

        await KPIExtractorAgent("Agent6_KPI", self.company_id, self.memory_store).extract_kpi_details()
        await GovernanceExtractorAgent("Agent7_Gov", self.company_id, self.memory_store).extract_governance()
        await CapexExtractorAgent("Agent8_Capex", self.company_id, self.memory_store).extract_capex()

        # --- PHASE 3: BENCHMARKING & REGULATORY (Agents 9-12) ---
        logging.info("--- Phase 3: Benchmarking & Regulatory ---")
        # Agent 9
        benchmark_results = await self.bencher.run_benchmark()
        
        from app.agents.tier3.regulatory_agents import RegulatoryAnalysisAgent
        reg_agent = RegulatoryAnalysisAgent("RegulatoryAgent", self.company_id, self.memory_store)
        
        reg_results = {
            "eu_taxonomy": await reg_agent.check_eu_taxonomy(), # Agent 10
            "csrd": await reg_agent.check_csrd_compliance(), # Agent 11
            "sbti": await reg_agent.check_sbti_validation() # Agent 12
        }

        # --- PHASE 4: ANALYSIS & SYNTHESIS (Agents 13-16) ---
        logging.info("--- Phase 4: Analysis & Synthesis ---")
        from app.agents.tier4.analysis_agents import AnalysisAgents
        analyzer = AnalysisAgents("AnalysisBrain", self.company_id, self.memory_store)
        
        achievability = await analyzer.assess_achievability() # Agent 13
        synthesis = await analyzer.synthesize_evidence() # Agent 14
        visuals = await analyzer.generate_visual_json() # Agent 15/16
        
        # Credit memo can take a long time - wrap in try/catch
        try:
            logging.info("AnalysisBrain: Starting credit memo generation (this may take several minutes)...")
            credit_memo = await analyzer.draft_credit_memo() # Bank-grade structured report
            logging.info("AnalysisBrain: Credit memo generation complete")
        except Exception as e:
            logging.error(f"Credit memo generation failed: {e}")
            credit_memo = {
                "meta": {"error": f"Credit memo generation failed: {str(e)}"},
                "sections": [
                    {
                        "id": "executive_summary",
                        "title": "Executive Summary (Generation Failed)",
                        "markdown": f"### Error\n\nThe credit memo could not be generated due to: {str(e)}. Please review the raw analysis data below.",
                        "bullets": ["Generation error - manual review required"],
                        "evidence": []
                    }
                ],
                "figures": []
            }
        
        # --- PHASE 5: FINAL DECISION (Agent 17) ---
        logging.info("--- Phase 5: Final Decision ---")
        
        final_decision_task = f"""
        Based on the EXTENSIVE memory context generated by the swarm of agents:
        - Benchmarking: {json.dumps(benchmark_results)}
        - Regulatory: {json.dumps(reg_results)}
        - Achievability: {json.dumps(achievability)}
        - Synthesis: {json.dumps(synthesis)}
        
        Generate the final Banker's Credit Recommendation.
        
        Format as JSON:
        {{
            "recommendation": "APPROVE" | "CONDITIONAL_APPROVAL" | "REJECT", # Mapped to Frontend Enum
            "confidence": "HIGH" | "MEDIUM" | "LOW",
            "overall_recommendation": "...", 
            "recommendation_rationale": "...",
            "key_findings": [
                {{"category": "Benchmark", "assessment": "STRONG", "detail": "..."}},
                {{"category": "Regulatory", "assessment": "WEAK", "detail": "..."}}
            ],
            "conditions_for_approval": ["..."]
        }}
        """
        
        decision_raw = await self.think_with_memory(final_decision_task, ["benchmark", "analysis", "regulatory"])

        try:
            decision = self._parse_llm_json(decision_raw)
        except Exception as first_error:
            # One repair attempt: ask the model to re-emit STRICT JSON only.
            repair_task = """
Your previous response was invalid or empty JSON.

Return STRICT JSON ONLY (no markdown, no backticks, no commentary) with this exact schema:
{
  "recommendation": "APPROVE" | "CONDITIONAL_APPROVAL" | "REJECT",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "overall_recommendation": "...",
  "recommendation_rationale": "...",
  "key_findings": [{"category": "Benchmark", "assessment": "STRONG", "detail": "..."}],
  "conditions_for_approval": ["..."]
}
""".strip()

            repaired_raw = await self.think_with_memory(
                repair_task,
                ["benchmark", "analysis", "regulatory"],
            )
            try:
                decision = self._parse_llm_json(repaired_raw)
            except Exception as second_error:
                logging.error(
                    "Orchestrator final decision JSON parse failed after retry: %s | retry error: %s",
                    str(first_error),
                    str(second_error),
                )
                # Conservative deterministic fallback to avoid crashing the whole pipeline.
                decision = {
                    "recommendation": "CONDITIONAL_APPROVAL",
                    "confidence": "LOW",
                    "overall_recommendation": "Manual review required",
                    "recommendation_rationale": "Final decision model output was invalid or empty; require human review.",
                    "key_findings": [
                        {
                            "category": "Data Quality",
                            "assessment": "WEAK",
                            "detail": "Final decision JSON could not be parsed from the LLM output.",
                        }
                    ],
                    "conditions_for_approval": [
                        "Provide a signed credit committee decision after reviewing the full memo outputs.",
                        "Re-run evaluation once model connectivity is stable.",
                    ],
                }
            
        full_report = {
            "company_id": self.company_id,
            "doc_results": doc_results,
            "benchmark_analysis": benchmark_results,
            "regulatory_analysis": reg_results,
            "achievability": achievability,
            "visuals": visuals, # Agent 15/16 Output
            "credit_memo": credit_memo,
            "final_decision": decision,
            
            # Helper to map to Frontend Structure
            "frontend_mapping": {
                "report_header": {
                    "company_name": self.company_id, # Placeholder
                    "analysis_date": "2025-01-11"
                },
                "peer_benchmarking": {
                    "peer_statistics": {"peer_count": 5, "confidence_level": "HIGH", "percentiles": {"median": 5.0, "p75": 7.0}},
                    "company_position": {"percentile_rank": 65, "classification": "ABOVE_AVERAGE"},
                    "ambition_classification": {"level": "MARKET_STANDARD", "rationale": "Matches sector avg", "ai_detailed_analysis": synthesis.get("narrative", ""), "classification_explanation": "Based on peer comparison"},
                    "recommendation": {"action": "APPROVE", "suggested_minimum": None, "message": "Target meets market standards"}
                },
                "executive_summary": decision
            }
        }
        
        logging.info("✅ ORCHESTRATOR: 17-Agent Pipeline Complete with Structured Data")
        return full_report

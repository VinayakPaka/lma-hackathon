from app.agents.base_agent import BaseAgent
import logging

class AchievementTrackerAgent(BaseAgent):
    """
    Tier 1 Agent: Historical Performance & Achievement.
    Tracks previous targets and execution history.
    """
    
    async def track_history(self):
        logging.info(f"{self.name}: Tracking historical achievements.")

        task = """
You are extracting HISTORICAL PERFORMANCE / TRACK RECORD evidence for a bank credit memo.

Scope:
- Identify any prior sustainability targets, interim milestones, and past performance statements.
- Include both: (a) explicit prior targets, and (b) historical KPI outcomes (e.g., YoY reductions) that demonstrate execution.

HARD RULES:
- Use only evidence present in memory.
- If no evidence exists, return an empty list and set score conservatively.
- Do NOT fabricate page numbers. If page markers exist, reference them exactly as "[PAGE N]".

Output STRICT JSON ONLY:
{
    "achievement_history": [
        {
            "period": "YYYY or YYYY-YYYY",
            "kpi_or_target": "...",
            "claimed_outcome": "MET|PARTIALLY_MET|MISSED|ONGOING|UNKNOWN",
            "metric_value": "... (optional)",
            "evidence": {
                "document_type": "...",
                "reference": "[PAGE N] / section title if available",
                "quote": "verbatim short quote"
            }
        }
    ],
    "track_record_score": 0,
    "track_record_rationale": "...",
    "limitations": ["..."]
}
"""
        
        # We rely on Agent 1's general extraction or raw text memories
        res = await self.think_with_memory(task, ["company_basics", "raw_extraction", "target"])
        
        # Use robust JSON parsing instead of raising exception
        data = self.parse_json_robust(res, "achievement_tracker")
        
        if data and "error" not in str(data).lower() and "achievement_history" in data:
            await self.remember("achievement", "track_record", data)
            return data
        else:
            # Return a default structure instead of failing
            logging.warning(f"AchievementTrackerAgent: Could not parse response, using default structure")
            default_data = {
                "achievement_history": [],
                "track_record_score": 0,
                "track_record_rationale": "Unable to extract historical performance data from documents. Manual review recommended.",
                "limitations": ["AI extraction failed - documents may require manual review"]
            }
            await self.remember("achievement", "track_record", default_data)
            return default_data

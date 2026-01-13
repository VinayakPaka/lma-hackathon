from app.agents.base_agent import BaseAgent
import logging

class CompletenessAnalyzerAgent(BaseAgent):
    """
    Tier 1 Agent: Document Completeness Analyzer.
    Checks for missing disclosures (CSRD gaps, etc.).
    """
    
    async def analyze_completeness(self):
        logging.info(f"{self.name}: Checking document completeness.")
        
        task = """
        Check if the following are present in memory.
        CRITICAL: You must cite WHERE each item is found (e.g. "Page 4, Table 2").
        
        1. Scope 1 & 2 Emissions (Found? Page?)
        2. Scope 3 Emissions (Found? Page?)
        3. Transition Plan (Found? Page?)
        4. Governance/Board info (Found? Page?)
        
        Return JSON: {
            "completeness_score": 0-100,
            "missing_items": ["Scope 3", "Auditor Name"],
            "evidence_map": {"scope1_2": "Page 4", "scope3": "Not Found"}
        }
        """
        
        res = await self.think_with_memory(task, ["baseline", "company_basics", "governance"])
        
        data = self.parse_json_robust(res, "completeness_analyzer")
        
        if data and "error" not in data:
            await self.remember("compliance", "completeness", data)
            return data
        else:
            return {"error": "Failed to parse completeness", "raw_response": res[:500] if res else ""}

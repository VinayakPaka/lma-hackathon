from app.agents.base_agent import BaseAgent
import logging

class GovernanceExtractorAgent(BaseAgent):
    """
    Tier 2 Agent: Governance & Incentive.
    Extracts board oversight mechanisms and executive comp.
    """
    
    async def extract_governance(self):
        logging.info(f"{self.name}: Extraction governance info.")
        
        task = """
        Review 'company_basics' and documents for Governance.
        1. Is there a Sustainability Committee on the Board?
        2. Is CEO compensation tied to ESG/Climate targets?
        
        CRITICAL: Provide evidence quote/location.
        
        Return JSON: {
            "board_oversight": true/false, 
            "ceo_incentive": true/false, 
            "details": "...",
            "evidence": "Page 34, Remuneration Report"
        }
        """
        
        res = await self.think_with_memory(task, ["governance", "company_basics"])
        
        data = self.parse_json_robust(res, "governance_extractor")
        
        if data and "error" not in data:
            await self.remember("governance", "structure", data)
            return data
        else:
            return {"error": "Failed parse", "raw_response": res[:500] if res else ""}

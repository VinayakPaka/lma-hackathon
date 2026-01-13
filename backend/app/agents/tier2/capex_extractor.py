from app.agents.base_agent import BaseAgent
import logging

class CapexExtractorAgent(BaseAgent):
    """
    Tier 2 Agent: Capital Expenditure Plan.
    Extracts budget, allocation, and financial realism.
    """
    
    async def extract_capex(self):
        logging.info(f"{self.name}: Extracting Capex info.")
        
        task = """
        Review 'company_basics' and documents for Capex/Investment.
        1. Total committed budget for transition?
        2. % of Revenue?
        
        CRITICAL: Provide evidence quote/location.
        
        Return JSON: {
            "total_budget": "...", 
            "percent_revenue": 0.0, 
            "projects": ["..."],
            "evidence": "Page 55, Financial Strategy"
        }
        """
        
        res = await self.think_with_memory(task, ["capex", "company_basics"])
        
        data = self.parse_json_robust(res, "capex_extractor")
        
        if data and "error" not in data:
            await self.remember("capex", "plan", data)
            return data
        else:
            return {"error": "Failed parse", "raw_response": res[:500] if res else ""}

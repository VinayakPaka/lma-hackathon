from app.agents.base_agent import BaseAgent
import logging

class BaselineVerificationAgent(BaseAgent):
    """
    Tier 1 Agent: Baseline Verification.
    Verifies the quality and audit status of the baseline data.
    """
    
    async def verify_baseline(self):
        logging.info(f"{self.name}: Verifying baseline data.")
        
        task = """
        Analyze the 'baseline' memory.
        1. Identify the baseline year and emissions value.
        2. Check if 'verified_by' or 'audit' is mentioned.
        3. Assign a Quality Score (1-5).
        
        CRITICAL: Cite the page number/section/table where verification is mentioned.
        
        Return JSON: 
        {
            "year": 0, "value": 0, "verified": false, "auditor": "", 
            "score": 0, 
            "evidence": "Page X, Audit Opinion"
        }
        """
        
        res = await self.think_with_memory(task, ["baseline", "verification"])
        
        data = self.parse_json_robust(res, "baseline_verifier")
        
        if data and "error" not in data:
            await self.remember("verification", "baseline_status", data)
            return data
        else:
            return {"error": "Failed to parse verification", "raw_response": res[:500] if res else ""}

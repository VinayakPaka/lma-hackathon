from app.agents.base_agent import BaseAgent
import logging

class RegulatoryAnalysisAgent(BaseAgent):
    """
    Tier 3 Combined Regulatory Agent (handling Taxonomy, CSRD, SBTi).
    Ideally split into 3 files, but combining for efficiency if logic is similar prompt-based checks.
    """
    
    async def check_eu_taxonomy(self):
        logging.info(f"{self.name}: Checking EU Taxonomy Alignment.")
        task = """
        Based on NACE code and Targets:
        1. Is the activity Taxonomy eligible?
        2. Does the target meet the substantial contribution criteria (e.g. < threshold)?
        
        CRITICAL: Provide evidence.
        
        Return JSON: {"eligible": true, "aligned": true/false, "gap": "...", "evidence": "..."}
        """
        res = await self.think_with_memory(task, ["company_basics", "target"])
        data = self.parse_json_robust(res, "eu_taxonomy")
        if data:
            await self.remember("regulatory", "eu_taxonomy", data)
        return data or {}

    async def check_csrd_compliance(self):
        logging.info(f"{self.name}: Checking CSRD Compliance.")
        task = """
        Review 'completeness' memory.
        Does the reporting cover E1, E2, S1, G1 standards?
        
        CRITICAL: Provide evidence.
        
        Return JSON: {"compliant": true/false, "score": 0-100, "evidence": "..."}
        """
        res = await self.think_with_memory(task, ["compliance"])
        data = self.parse_json_robust(res, "csrd_compliance")
        if data:
            await self.remember("regulatory", "csrd", data)
        return data or {}

    async def check_sbti_validation(self):
        logging.info(f"{self.name}: Checking SBTi Status.")
        task = """
        Is there any mention of 'SBTi' or 'Science Based Targets' validation or commitment?
        
        CRITICAL: Provide evidence (e.g. "SBTi dashboard status: Committed").
        
        Return JSON: {"validated": true/false, "status": "committed/targets_set/none", "evidence": "..."}
        """
        res = await self.think_with_memory(task, ["company_basics", "target"])
        data = self.parse_json_robust(res, "sbti_validation")
        if data:
            await self.remember("regulatory", "sbti", data)
        return data or {}

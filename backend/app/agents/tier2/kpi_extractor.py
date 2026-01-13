from app.agents.base_agent import BaseAgent
import logging

class KPIExtractorAgent(BaseAgent):
    """
    Tier 2 Agent: KPI Target Extraction.
    Specializes in parsing complex KPI definitions (absolute vs intensity, scopes).
    """
    
    async def extract_kpi_details(self):
        logging.info(f"{self.name}: Refining KPI target extraction.")
        
        task = """
        Analyze the 'kpi_targets' memory.
        Refine into specific structure.
        
        CRITICAL: Cite the source document/page for the target definition.
        
        Return JSON: 
        {
            "type": "...", "scopes": [1,2], "value": 0.0, "unit": "%",
            "evidence": "Page 12, Sustainability Report"
        }
        """
        
        res = await self.think_with_memory(task, ["target", "doc_metadata"])
        
        data = self.parse_json_robust(res, "kpi_extractor")
        
        if data and "error" not in data:
            await self.remember("target", "refined_kpi", data)
            return data
        else:
            return {"error": "Failed parse", "raw_response": res[:500] if res else ""}

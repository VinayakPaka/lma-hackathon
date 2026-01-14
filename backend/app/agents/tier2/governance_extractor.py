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
You are extracting governance and accountability structures for ESG/climate oversight.

Review ALL available memory context for governance indicators:

KEY GOVERNANCE ELEMENTS TO IDENTIFY:
1. **Board-Level Climate Oversight**
   - Dedicated Sustainability/ESG Committee on the Board
   - Climate responsibilities assigned to specific Board committee
   - Frequency of Board ESG discussions

2. **Executive Accountability**
   - CEO/C-suite compensation tied to ESG/climate KPIs
   - Percentage of variable compensation linked to sustainability
   - Specific ESG metrics in executive scorecards

3. **Sustainability Committee/Function**
   - Dedicated Chief Sustainability Officer (CSO)
   - Sustainability department/team structure
   - Reporting line to Board

4. **Risk Management Integration**
   - Climate risks in enterprise risk framework
   - TCFD alignment in disclosures

ASSESSMENT APPROACH:
- If explicit governance disclosure found, extract specific details
- If NO explicit disclosure, note as "Not evidenced in provided documents"
- Distinguish between "not found" (may exist but not disclosed) vs "confirmed absent"

CRITICAL: If data is missing, clearly state what is missing and what would be needed.

Return JSON:
{
    "board_oversight": true/false,
    "board_oversight_details": "Specific committee names, responsibilities, meeting frequency if found...",
    "ceo_incentive": true/false,
    "ceo_incentive_details": "Percentage of compensation, specific KPIs if found...",
    "sustainability_committee": true/false,
    "sustainability_committee_details": "Structure and reporting line if found...",
    "confidence": "HIGH|MEDIUM|LOW",
    "evidence": "Page/section references or 'Not evidenced in provided documents'",
    "missing_information": ["List of key governance elements not found in documents..."]
}
        """
        
        res = await self.think_with_memory(task, ["governance", "company_basics", "raw_extraction", "document_metadata"])
        
        data = self.parse_json_robust(res, "governance_extractor")
        
        # Ensure we always have a structured response
        if not data or "error" in data:
            data = {
                "board_oversight": False,
                "board_oversight_details": "Not evidenced in provided documents",
                "ceo_incentive": False,
                "ceo_incentive_details": "Not evidenced in provided documents",
                "sustainability_committee": False,
                "sustainability_committee_details": "Not evidenced in provided documents",
                "confidence": "LOW",
                "evidence": "Insufficient governance disclosure in provided documents",
                "missing_information": [
                    "Board-level climate/ESG committee structure",
                    "Executive compensation linkage to ESG targets",
                    "Sustainability governance framework"
                ]
            }
        
        await self.remember("governance", "structure", data)
        return data

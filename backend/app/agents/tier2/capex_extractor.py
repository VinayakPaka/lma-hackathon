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
You are extracting capital expenditure (CapEx) and financial commitment information for decarbonization.

Review ALL available memory context for financial commitment indicators:

KEY FINANCIAL ELEMENTS TO IDENTIFY:
1. **Total Transition Budget**
   - Committed CapEx for decarbonization/sustainability
   - Multi-year investment plan amounts
   - Green CapEx as percentage of total CapEx

2. **Revenue Allocation**
   - Percentage of revenue dedicated to transition
   - Sustainability R&D spending
   - Green bond/loan proceeds allocation

3. **Project-Specific Investments**
   - Renewable energy installations
   - Energy efficiency upgrades
   - Fleet electrification
   - Process/technology upgrades
   - Carbon capture/offset programs

4. **Timeline and Milestones**
   - Investment timeline (e.g., 2024-2030)
   - Annual spending projections
   - Key project milestones

ASSESSMENT APPROACH:
- If explicit CapEx disclosure found, extract specific amounts and projects
- If NO explicit disclosure, note as "Not evidenced in provided documents"
- Look for indirect indicators (mentions of investments, projects, initiatives)

CRITICAL: If data is missing, clearly state what is missing and what would be needed.

Return JSON:
{
    "total_budget": "Amount in currency or 'Not disclosed'",
    "budget_currency": "EUR|USD|GBP|...",
    "percent_revenue": 0.0,
    "percent_capex": 0.0,
    "projects": [
        {"name": "Project name", "amount": "Amount if known", "timeline": "Timeline if known"}
    ],
    "timeline": "Investment period if disclosed",
    "confidence": "HIGH|MEDIUM|LOW",
    "evidence": "Page/section references or 'Not evidenced in provided documents'",
    "missing_information": ["List of key CapEx elements not found in documents..."]
}
        """
        
        res = await self.think_with_memory(task, ["capex", "company_basics", "raw_extraction", "document_metadata"])
        
        data = self.parse_json_robust(res, "capex_extractor")
        
        # Ensure we always have a structured response
        if not data or "error" in data:
            data = {
                "total_budget": "Not disclosed",
                "budget_currency": "Unknown",
                "percent_revenue": 0.0,
                "percent_capex": 0.0,
                "projects": [],
                "timeline": "Not disclosed",
                "confidence": "LOW",
                "evidence": "Insufficient CapEx disclosure in provided documents",
                "missing_information": [
                    "Total decarbonization CapEx budget",
                    "Project-specific investment details",
                    "Multi-year investment timeline"
                ]
            }
        
        await self.remember("capex", "plan", data)
        return data

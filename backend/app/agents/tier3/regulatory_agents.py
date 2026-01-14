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
You are assessing EU Taxonomy alignment for a sustainability-linked loan.

Review ALL available memory context for EU Taxonomy indicators:
1. NACE codes or economic activity classification
2. Climate change mitigation/adaptation objectives
3. Substantial contribution criteria (emissions thresholds, reduction targets)
4. Do No Significant Harm (DNSH) criteria
5. Minimum safeguards compliance

ASSESSMENT APPROACH:
- If explicit EU Taxonomy disclosure is found, assess against technical screening criteria
- If NO explicit disclosure, evaluate based on:
  * Industry sector alignment with Taxonomy-eligible activities
  * GHG reduction targets compared to sector benchmarks
  * Presence of transition plan elements
  * Third-party verification or SBTi validation as proxy indicators

CLASSIFICATION:
- "verified": Explicit EU Taxonomy disclosure with evidence
- "likely_eligible": Strong indicators but no formal disclosure
- "not_verified": Insufficient data to assess
- "not_eligible": Evidence suggests non-alignment

CRITICAL: Always provide a reasoned assessment even when data is incomplete.

Return JSON:
{
    "eligible": true/false,
    "aligned": true/false,
    "status": "verified|likely_eligible|not_verified|not_eligible",
    "confidence": "HIGH|MEDIUM|LOW",
    "gap": "Detailed gap description if not aligned...",
    "evidence": "Specific evidence or explanation of assessment basis...",
    "recommendation": "What additional information would strengthen this assessment..."
}
        """
        res = await self.think_with_memory(task, ["company_basics", "target", "regulatory", "raw_extraction", "document_metadata"])
        data = self.parse_json_robust(res, "eu_taxonomy")
        
        # Ensure we always have a structured response
        if not data:
            data = {
                "eligible": False,
                "aligned": False,
                "status": "not_verified",
                "confidence": "LOW",
                "gap": "Insufficient data provided for EU Taxonomy assessment",
                "evidence": "No explicit EU Taxonomy disclosure found in provided documents",
                "recommendation": "Request formal EU Taxonomy alignment disclosure from borrower"
            }
        
        await self.remember("regulatory", "eu_taxonomy", data)
        return data

    async def check_csrd_compliance(self):
        logging.info(f"{self.name}: Checking CSRD Compliance.")
        task = """
You are assessing CSRD (Corporate Sustainability Reporting Directive) compliance.

Review ALL available memory context for CSRD/ESRS indicators:

ESRS STANDARDS TO CHECK:
- E1: Climate change (GHG emissions, targets, transition plan)
- E2: Pollution
- E3: Water and marine resources
- E4: Biodiversity and ecosystems
- E5: Resource use and circular economy
- S1: Own workforce
- S2: Workers in value chain
- S3: Affected communities
- S4: Consumers and end-users
- G1: Business conduct (governance, ethics)

ASSESSMENT APPROACH:
- If formal CSRD/sustainability report is referenced, evaluate coverage
- If NO formal CSRD report, assess based on:
  * Company jurisdiction (EU companies >500 employees required from 2024)
  * Available sustainability disclosures against ESRS requirements
  * Presence of GHG reporting (E1 minimum)
  * Governance disclosures (G1 minimum)

SCORING:
- 80-100: Comprehensive ESRS coverage (8+ standards addressed)
- 60-79: Substantial coverage (5-7 standards addressed)
- 40-59: Partial coverage (3-4 standards addressed)
- 20-39: Limited coverage (1-2 standards addressed)
- 0-19: Minimal/no CSRD-aligned reporting

CLASSIFICATION:
- "compliant": Score >= 60 with formal CSRD report
- "partial": Score 40-59 or informal sustainability reporting
- "not_verified": Insufficient data to assess
- "non_compliant": Score < 40 or no sustainability reporting

CRITICAL: Always provide a reasoned assessment even when data is incomplete.

Return JSON:
{
    "compliant": true/false,
    "status": "compliant|partial|not_verified|non_compliant",
    "score": 0-100,
    "confidence": "HIGH|MEDIUM|LOW",
    "standards_covered": ["E1", "G1", ...],
    "gaps": ["E2 - Pollution not addressed", ...],
    "evidence": "Specific evidence or explanation of assessment basis...",
    "recommendation": "What additional information would strengthen this assessment..."
}
        """
        res = await self.think_with_memory(task, ["compliance", "company_basics", "raw_extraction", "document_metadata", "governance"])
        data = self.parse_json_robust(res, "csrd_compliance")
        
        # Ensure we always have a structured response
        if not data:
            data = {
                "compliant": False,
                "status": "not_verified",
                "score": 0,
                "confidence": "LOW",
                "standards_covered": [],
                "gaps": ["Unable to assess - no CSRD-aligned reporting provided"],
                "evidence": "No formal CSRD or sustainability report found in provided documents",
                "recommendation": "Request CSRD-aligned sustainability report or equivalent disclosures"
            }
        
        await self.remember("regulatory", "csrd", data)
        return data

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

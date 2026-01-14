from app.agents.base_agent import BaseAgent
import logging
import asyncio
import os
import json
import concurrent.futures
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


CREDIT_MEMO_JSON_SCHEMA_HINT = """
Return STRICT JSON ONLY with this shape:
{
    "meta": {
        "report_title": "KPI Assessment Credit Memo",
        "prepared_for": "Credit Committee",
        "prepared_by": "GreenGuard ESG Analyst (AI-assisted)",
        "as_of_date": "YYYY-MM-DD",
        "version": "1.0"
    },
    "inputs_summary": {
        "company_name": "...",
        "industry_sector": "...",
        "loan_type": "...",
        "facility_amount": "...",
        "tenor_years": 0,
        "kpi": {
            "metric": "GHG Emissions Reduction",
            "target_value": 0,
            "target_unit": "%",
            "baseline_value": 0,
            "baseline_year": 0,
            "target_year": 0,
            "emissions_scope": "Scope 1+2|Scope 1+2+3|Scope 3|Unknown"
        }
    },
    "data_quality": {
        "documents_reviewed": [{"document_type": "...", "status": "provided|missing|unreadable", "notes": "..."}],
        "evidence_gaps": ["..."],
        "confidence": "HIGH|MEDIUM|LOW"
    },
    "sections": [
        {
            "id": "executive_summary",
            "title": "Executive Summary",
            "markdown": "...",
            "bullets": ["..."],
            "evidence": [{"source": "document|benchmark|banker_input", "reference": "...", "snippet": "..."}]
        }
    ],
    "figures": [
        {
            "id": "fig_peer_comparison",
            "title": "Peer Benchmarking (Reduction Target vs Peers)",
            "type": "bar",
            "data": {"labels": ["Company Target", "Peer Median", "Top Quartile"], "dataset": [{"label": "Reduction %", "data": [0, 0, 0]}]}
        },
        {
            "id": "fig_trajectory",
            "title": "Emissions Trajectory (Indexed)",
            "type": "line",
            "data": {"labels": ["2020", "2025", "2030"], "data": [100, 80, 50]}
        }
    ],
    "risk_register": [{
        "id": "R1",
        "severity": "HIGH|MEDIUM|LOW",
        "theme": "Data|Execution|Regulatory|Reputational|Financial",
        "description": "...",
        "mitigant": "...",
        "covenant_or_condition": "...",
        "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]
    }],
    "recommended_terms": {
        "decision": "APPROVE|CONDITIONAL_APPROVAL|REJECT|MANUAL_REVIEW",
        "conditions": ["..."],
        "monitoring_plan": ["..."],
        "covenants": ["..."]
    }
}
"""

class AnalysisAgents(BaseAgent):
    """
    Tier 4: Analysis & Synthesis.
    Proprietary risk modeling and report synthesis.
    """
    
    def _create_fallback_memo(self, error_msg: str) -> dict:
        """Create a fallback credit memo when AI generation fails."""
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "meta": {
                "report_title": "KPI Assessment Credit Memo",
                "prepared_for": "Credit Committee",
                "prepared_by": "GreenGuard ESG Analyst (Fallback Mode)",
                "as_of_date": today,
                "version": "1.0",
                "models_used": ["Fallback"],
                "error": error_msg
            },
            "inputs_summary": {
                "company_name": "Unknown",
                "industry_sector": "Unknown",
                "loan_type": "Sustainability-Linked Loan",
                "facility_amount": "Not specified",
                "tenor_years": 0,
                "kpi": {
                    "metric": "GHG Emissions Reduction",
                    "target_value": 0,
                    "target_unit": "%",
                    "baseline_value": 0,
                    "baseline_year": 0,
                    "target_year": 0,
                    "emissions_scope": "Unknown"
                }
            },
            "data_quality": {
                "documents_reviewed": [],
                "evidence_gaps": ["AI generation failed - manual review required"],
                "confidence": "LOW"
            },
            "sections": [
                {
                    "id": "executive_summary",
                    "title": "Executive Summary",
                    "markdown": f"### Generation Error\n\nThe credit memo could not be generated automatically due to: {error_msg}.\n\nPlease review the raw data and individual agent outputs for the assessment.",
                    "bullets": ["AI generation failed", "Manual review required", f"Error: {error_msg}"],
                    "evidence": []
                }
            ],
            "figures": [],
            "risk_register": [],
            "recommended_terms": {
                "decision": "MANUAL_REVIEW",
                "conditions": ["Complete manual assessment required"],
                "monitoring_plan": ["TBD after manual review"],
                "covenants": ["TBD after manual review"]
            }
        }
    
    async def assess_achievability(self):
        logging.info(f"{self.name}: Assessing Achievability & Risk.")
        task = """
You are conducting a COMPREHENSIVE achievability and credibility assessment for a bank credit memo.

Synthesize ALL available evidence from Capex plans, Governance structures, Track Record, and Target information to produce a DETAILED assessment.

ASSESSMENT FRAMEWORK:
1. **Track Record Analysis** (Weight: 30%)
   - Has the company met previous sustainability targets?
   - What is the historical emissions reduction trajectory?
   - Are there any missed targets or delays?

2. **Governance & Accountability** (Weight: 25%)
   - Is there board-level oversight of climate/ESG targets?
   - Are executive compensation incentives tied to ESG performance?
   - Is there a dedicated sustainability committee?

3. **Financial Commitment / CapEx** (Weight: 20%)
   - What is the committed budget for decarbonization?
   - What percentage of revenue/CapEx is allocated to transition?
   - Are there specific projects with timelines?

4. **External Validation** (Weight: 15%)
   - SBTi validation status (committed, targets set, none)?
   - Third-party verification of emissions data?
   - Second Party Opinions from rating agencies?

5. **Transition Plan Quality** (Weight: 10%)
   - Is there a detailed, credible transition plan?
   - Are milestones and interim targets defined?
   - Is the methodology clear and auditable?

SCORING GUIDE:
- Score 80-100: HIGH credibility - Strong evidence across all dimensions
- Score 50-79: MEDIUM credibility - Mixed evidence, some gaps
- Score 0-49: LOW credibility - Significant gaps or missing evidence

HARD RULES:
- Use only evidenced facts from memory.
- If evidence is missing, explicitly mark it "Not evidenced" and explain what would be needed.
- Provide DETAILED reasoning with specific data points and citations.

Return STRICT JSON only:
{
    "score": 0,
    "credibility_level": "HIGH|MEDIUM|LOW",
    "signals": {
        "sbti_validation": {"detected": false, "evidence": "Detailed evidence description with source..."},
        "third_party_verified": {"detected": false, "evidence": "..."},
        "transition_plan": {"detected": false, "evidence": "..."},
        "board_oversight": {"detected": false, "evidence": "..."},
        "past_targets_met": {"detected": false, "evidence": "..."},
        "capex_commitment": {"detected": false, "evidence": "..."},
        "management_incentives": {"detected": false, "evidence": "..."}
    },
    "top_risks": [
        {"severity": "HIGH|MEDIUM|LOW", "category": "Execution|Data|Regulatory|Financial", "issue": "Detailed description of the risk...", "recommendation": "Specific mitigation recommendation...", "evidence": "Source of risk identification..."}
    ],
    "reasoning": "COMPREHENSIVE multi-paragraph explanation of the credibility assessment, covering each dimension with specific data points, percentages, and citations where available. This should be 300-500 words minimum, written in professional banking memo style.",
    "evidence": ["List of all evidence sources used in this assessment with specific citations..."]
}
"""
        res = await self.think_with_memory(task, ["capex", "governance", "achievement", "target", "raw_extraction", "regulatory"])
        
        data = self.parse_json_robust(res, "achievability")
        
        if data and "score" in data:
            await self.remember("analysis", "achievability", data)
            return data
        else:
            logging.error(f"Tier4 achievability failed: Could not parse response. Preview: {res[:300] if res else 'Empty'}")
            # Return a safe fallback instead of crashing
            return {
                "score": 0,
                "credibility_level": "LOW",
                "signals": {},
                "top_risks": [],
                "reasoning": "Assessment failed due to AI provider error.",
                "evidence": []
            }

    async def synthesize_evidence(self):
        logging.info(f"{self.name}: Synthesizing Evidence.")
        task = """
You are drafting a COMPREHENSIVE executive-summary style narrative for a bank credit memo.

This narrative will be the primary content read by the Credit Committee. It must be:
- DETAILED (minimum 500 words)
- EVIDENCE-BASED with specific citations
- ACTIONABLE with clear recommendations
- PROFESSIONAL in banking memo style

NARRATIVE STRUCTURE:
1. **Company Overview & Transaction Context** (1-2 paragraphs)
   - Company name, sector, and business description
   - Loan type and sustainability-linked nature
   - KPI target and timeline summary

2. **Target Ambition Assessment** (2-3 paragraphs)
   - Comparison to sector peers (cite specific percentages and peer counts)
   - Comparison to SBTi pathway requirements
   - Classification rationale (WEAK/MODERATE/AMBITIOUS)
   - Specific numeric benchmarks from memory

3. **Credibility & Achievability Analysis** (2-3 paragraphs)
   - Track record of meeting past targets (with specific data)
   - Governance and accountability structures
   - Financial commitment and CapEx plans
   - External validations (SBTi, third-party verification)

4. **Key Risks & Mitigants** (1-2 paragraphs)
   - Top 3-5 risks identified
   - Proposed mitigants and covenant structures
   - Monitoring and reporting requirements

5. **Recommendation Summary** (1 paragraph)
   - Clear recommendation (APPROVE/CONDITIONAL_APPROVAL/REJECT)
   - Key conditions for approval
   - Rationale for decision

6. **STYLE GUIDELINES:**
   - Tone: Professional, objective, "Investment Banking Credit Memo" style.
   - Formatting: STRICTLY split the output into 2-3 distinct paragraphs. Do NOT produce one giant wall of text.
   - Avoid flowery language; be direct and data-driven.

HARD RULES:
- Do not fabricate citations - use [PAGE N] only if page references exist in memory
- If page/section references are unavailable, cite the source type (e.g., "banker_input", "benchmark", "spo_document")
- Include SPECIFIC NUMBERS: percentages, peer counts, emission values where available
- Be balanced - highlight both strengths and concerns
- **CRITICAL**: Ensure the `narrative` field contains line breaks (`\n\n`) between paragraphs.

Return STRICT JSON only:
{
    "narrative": "COMPREHENSIVE multi-paragraph narrative (500+ words) following the structure above...",
    "evidence": [
        {"source": "document|benchmark|banker_input", "reference": "Specific location or category", "snippet": "Key quote or data point"},
        {"source": "...", "reference": "...", "snippet": "..."}
    ]
}
"""
        res = await self.think_with_memory(task, ["benchmark", "regulatory", "analysis", "achievement", "raw_extraction", "target", "banker_input"])
        
        data = self.parse_json_robust(res, "synthesize_evidence")
        
        if data and "narrative" in data:
            await self.remember("analysis", "synthesis", data)
            return data
        else:
            logging.error(f"Tier4 synthesis failed: Could not parse response. Preview: {res[:300] if res else 'Empty'}")
            return {
                "narrative": "Error generating synthesis narrative due to AI provider failure.",
                "evidence": []
            }

    async def generate_visual_json(self):
        # Generates structure for Frontend Charts (e.g. Recharts)
        logging.info(f"{self.name}: Generating Visual Chart Data.")

        task = """
Generate chart-ready JSON for the frontend visualization.

HARD RULES:
- Use only benchmark/target numbers that exist in memory.
- Pull actual values from the SBTi peer benchmark data and target information.
- If missing, use 0 and note limitations elsewhere.

Return STRICT JSON only:
{
    "peer_comparison": {
        "labels": ["Company Target", "Peer Median", "Top Quartile"],
        "dataset": [{"label": "Reduction %", "data": [0, 0, 0]}]
    },
    "emissions_trajectory": {
        "labels": ["2020", "2025", "2030"],
        "data": [100, 80, 50]
    }
}
"""
        res = await self.think_with_memory(task, ["benchmark", "target"])
        
        data = self.parse_json_robust(res, "generate_visual_json")
        
        if data and ("peer_comparison" in data or "emissions_trajectory" in data):
            await self.remember("analysis", "visuals", data)
            return data
        else:
            logging.error(f"Tier4 visuals failed: Could not parse response. Preview: {res[:300] if res else 'Empty'}")
            return {
                "peer_comparison": {
                    "labels": ["Error"], 
                    "dataset": [{"label": "Reduction %", "data": [0]}]
                },
                "emissions_trajectory": {
                    "labels": ["Error"],
                    "data": [0]
                }
            }

    async def draft_credit_memo(self):
        """
        Generate a credit memo using the base agent's robust fallback chain.
        Executes sections in parallel using the configured unified LLM logic.
        """
        logging.info(f"{self.name}: Starting Credit Memo Generation via Unified LLM Logic")
        
        # Gather memory context
        memory_context = ""
        for category in ["banker_input", "target", "benchmark", "regulatory", "analysis", "achievement", "raw_extraction", "document_metadata"]:
            memories = await self.memory.retrieve_memory(query="credit memo generation", category=category)
            if memories:
                memory_context += f"\n[{category.upper()}]:\n"
                for mem in memories:
                    memory_context += f"- {mem}\n"
        
        # Define tasks
        task_strategic = """Generate these 3 credit memo sections as a JSON array.

SECTION 1: executive_summary (500-700 words)
Write a comprehensive executive summary following this EXACT structure:

## 📘 Sustainability-Linked Loan KPI Ambition & Achievability Assessment

**Transaction Context:**
- Borrower: [Company Name]
- Sector: [Industry] | Region: [Geography] 
- Proposed Facility: [Loan Amount] Sustainability-Linked Loan
- Tenor: [Years] | Margin Adjustment: [±X bps]

**Detailed Report Overview:**
State that this report assesses whether the borrower's emissions-reduction KPI is ambitious and achievable, in line with EU green-lending expectations, ICMA Sustainability-Linked Loan Principles.

**Headline Conclusion:**
Create a blockquote with the key finding:
> [Company]'s KPI is [HIGHLY AMBITIOUS/AMBITIOUS/MARKET-ALIGNED/BELOW MARKET], [CREDIBLE/PARTIALLY CREDIBLE/NOT CREDIBLE], and [status of target achievement].
> [Key implication for credit decision and pricing].

**KPI Under Review:**
Create a table:
| Element | Value |
|---------|-------|
| Metric | [e.g., Absolute GHG emissions (tCO2e)] |
| Scope | [Scope 1/2/3 coverage] |
| Baseline Year | [Year] |
| Baseline Value | [Value with unit] |
| Target Year | [Year] |
| Target Value | [Reduction %] |

**Why This KPI Matters for Bankers:**
Explain materiality, auditability, and regulatory preference for this type of KPI.

SECTION 2: risks (400-500 words)
Write a detailed risk assessment with this structure:

## 7. Risk Flags Review

Create a summary risk table:
| Risk Area | Banker View |
|-----------|-------------|
| Baseline credibility | 🟢 Strong / 🟡 Moderate / 🔴 Weak |
| Data verification | 🟢 Audited / 🟡 Self-reported / 🔴 Unverified |
| Scope 3 controllability | 🟢 Proven / 🟡 Partial / 🔴 Limited |
| Execution risk | 🟢 Very low / 🟡 Moderate / 🔴 High |
| Reputational risk | 🟢 Minimal / 🟡 Moderate / 🔴 Elevated |

For each risk, provide:
- Risk description
- Current status assessment
- Mitigating factors
- Residual risk level

Conclude with: "No material ESG or KPI-related red flags identified" or list specific flags.

SECTION 3: recommendation (400-500 words)
Write the final credit recommendation with this structure:

## 8. Final Credit Recommendation

### KPI Classification
State the classification clearly:
> [HIGHLY AMBITIOUS & ACHIEVED / AMBITIOUS & ON-TRACK / MARKET-ALIGNED / BELOW MARKET]

### Target Ambition Assessment
Provide explicit assessment:
- Percentile ranking vs peers
- Alignment with science-based pathways
- Comparison to sector benchmarks

### Loan Decision Guidance
Provide clear guidance:
- Decision: APPROVE / CONDITIONAL APPROVAL / REJECT
- Eligible for favorable pricing: Yes/No
- Margin step-up risk: Remote/Moderate/Elevated
- Green portfolio eligibility: Yes/No with justification

### Conditions Precedent (if applicable)
List 3-5 specific conditions

### Conditions Subsequent (if applicable)
List 3-5 ongoing monitoring requirements

### One-Line Credit Memo Summary
Provide a single sentence summary suitable for credit committee:
> "[Company] presents a [description] KPI that is [validation status], [peer comparison], and [achievement status], resulting in [risk level]."

Return STRICT JSON only:
[
    {"id": "executive_summary", "title": "Executive Summary", "markdown": "...", "bullets": ["..."], "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]},
    {"id": "risks", "title": "Risk Assessment", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "recommendation", "title": "Credit Recommendation and Terms", "markdown": "...", "bullets": ["..."], "evidence": [...]}
]"""
        
        task_analytical = """Generate these 3 credit memo sections as a JSON array.

SECTION 1: kpi_definition (300-400 words)
Write the KPI Definition section with this structure:

## 1. KPI Definition & Transaction Context

### KPI Under Review
Create a structured overview:
- Metric: [Full metric name]
- Scope: [Scope 1 + Scope 2 + Scope 3 coverage details]
- Methodology: [GHG Protocol or other standard]
- Baseline Year: [Year]
- Baseline Value: [Absolute value with tCO2e unit]

### Targets Table
| Target Horizon | Target Value | Reduction vs Baseline |
|----------------|--------------|----------------------|
| [Interim Year] | [Value] | [%] |
| [Long-term Year] | [Value] | [%] |

### Why This KPI Matters for Bankers
Explain:
- Materiality to business operations
- Auditability and manipulation resistance
- Regulatory preference (EU EBA, ICMA SLLP)
- Comparison to intensity-based alternatives

SECTION 2: benchmarking (500-600 words)
Write a 5-layer benchmarking analysis:

## 3. Peer Benchmarking & Ambition Analysis

### Banker Question:
> "Is this target aggressive relative to peers and science?"

### Layer 1 - Sector Benchmark
- Company target vs Eurostat/industry sector average
- Specific percentages and gap analysis
- Conclusion: 🟢 POSITIVE / 🟡 NEUTRAL / 🔴 NEGATIVE

### Layer 2 - Size Adjustment
- Company size context (large cap expectations vs SME)
- Resource availability for transition
- Conclusion: 🟢 POSITIVE / 🟡 NEUTRAL / 🔴 NEGATIVE

### Layer 3 - Geography Adjustment
- Country renewable energy mix percentage
- Regional regulatory environment (EU ETS, national policies)
- Conclusion: 🟢 POSITIVE / 🟡 NEUTRAL / 🔴 NEGATIVE

### Layer 4 - Comparable Peer Analysis
Create a comparison with SBTi peers:
- Peer count and confidence level
- Peer median and P75 percentile values
- Company's percentile rank
- Conclusion: 🟢 POSITIVE / 🟡 NEUTRAL / 🔴 NEGATIVE

### Layer 5 - Climate Pathway Alignment
- IEA/SBTi pathway requirements for sector
- Gap to 1.5°C or 2°C alignment
- Net-Zero commitment status
- Conclusion: 🟢 POSITIVE / 🟡 NEUTRAL / 🔴 NEGATIVE

### Final Ambition Classification
State clearly: HIGHLY AMBITIOUS (>75th percentile) / AMBITIOUS (50-75th) / MARKET-ALIGNED (25-50th) / BELOW MARKET (<25th)

SECTION 3: track_record (300-400 words)
Write the performance assessment:

## 4. Performance vs Target (Reality Check)

### Banker Question:
> "Has the company demonstrated it can deliver on emissions targets?"

### Current Performance Table
| Metric | Result |
|--------|--------|
| Current Year Emissions | [Value tCO2e] |
| Reduction vs Baseline | [%] |
| Interim Target | [%] |
| Status | ✅ Exceeded / 🟡 On Track / ❌ Behind |

### Scope-Level Results
Provide year-over-year breakdown:
- Scope 1: [% change]
- Scope 2: [% change]  
- Scope 3: [% change] (if applicable)

### Historical Target Achievement
List past targets and outcomes:
- [Year] Target: [Met/Partially Met/Missed]
- [Year] Target: [Met/Partially Met/Missed]

### Banker Interpretation
Summarize with signals:
✅ Execution capability proven / ❌ Execution concerns
✅ KPI not "easy" or cosmetic / ❌ Target appears unambitious
✅ Downside risk minimal / ❌ Elevated downside risk

Return STRICT JSON only:
[
    {"id": "kpi_definition", "title": "KPI Definition & Boundary", "markdown": "...", "bullets": ["..."], "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]},
    {"id": "benchmarking", "title": "5-Layer Benchmarking Analysis", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "track_record", "title": "Historical Performance / Track Record", "markdown": "...", "bullets": ["..."], "evidence": [...]}
]"""
        
        task_data = """Generate these 4 credit memo sections as a JSON array.

SECTION 1: documents_reviewed (200-300 words)
Write the documents analysis section:

## 2. Baseline Integrity & Data Quality (Foundation Check)

### Banker Question:
> "Is the starting point real, recent, audited, and defensible?"

### Documents Analyzed Table
| Document Type | Status | Data Quality |
|--------------|--------|--------------|
| CSRD/Sustainability Report | ✅ Provided / ❌ Missing | HIGH/MEDIUM/LOW |
| Financial Statements | ✅ Provided / ❌ Missing | HIGH/MEDIUM/LOW |
| Second-Party Opinion | ✅ Provided / ❌ Missing | HIGH/MEDIUM/LOW |
| SBTi Validation | ✅ Provided / ❌ Missing | HIGH/MEDIUM/LOW |

### Assessment
- Baseline year assessment (pre-COVID preferred)
- Scope coverage (1-2-3)
- Methodology consistency
- External assurance status
- Reporting history

### Banker Signals
❌ No baseline inflation / ✅ Baseline inflation concerns
❌ No outdated data / ✅ Data staleness concerns  
✅ Long reporting history / ❌ Limited reporting history

### Conclusion:
✅ Baseline quality: STRONG / REGULATOR-DEFENSIBLE
or
🟡 Baseline quality: MODERATE / REQUIRES VERIFICATION
or
❌ Baseline quality: WEAK / NOT DEFENSIBLE

SECTION 2: extracted_data (300-400 words)
Write the extracted data section:

## Extracted KPI & Governance Data

### Emissions Data
| Metric | Value | Year | Status |
|--------|-------|------|--------|
| Scope 1 | [tCO2e] | [Year] | Evidenced/Not Evidenced |
| Scope 2 | [tCO2e] | [Year] | Evidenced/Not Evidenced |
| Scope 3 | [tCO2e] | [Year] | Evidenced/Not Evidenced |
| Total | [tCO2e] | [Year] | Evidenced/Not Evidenced |

### Target Information
| Element | Value | Status |
|---------|-------|--------|
| Reduction Target | [%] | Evidenced |
| Interim Target | [%] by [Year] | Evidenced/Not Evidenced |
| Base Year | [Year] | Evidenced |
| Target Year | [Year] | Evidenced |

### Governance Findings
| Element | Finding | Status |
|---------|---------|--------|
| Board Climate Oversight | Yes/No + details | Evidenced/Not Evidenced |
| Sustainability Committee | Yes/No + details | Evidenced/Not Evidenced |
| Executive ESG Compensation | [%] linked | Evidenced/Not Evidenced |
| Third-Party Verification | [Auditor name] | Evidenced/Not Evidenced |

SECTION 3: credibility_signals (400-500 words)
Write the achievability assessment:

## 5. Achievability Assessment (Core Credit Question)

### Capital & Operational Levers
List specific decarbonization initiatives:
- Renewable energy procurement
- Energy efficiency programs
- Supply chain engagement
- Fleet electrification
- Technology investments

### Governance & Incentives
- Board-level ESG oversight: Yes/No
- Executive compensation linked to decarbonization: Yes/No with %
- Annual external verification: Yes/No
- Net-Zero commitment: Yes/No

### Track Record (Strongest Signal)
- Emissions reduction achieved to date: [%]
- Target achievement history
- Consistency of delivery

### Credibility Signal Assessment Table
| Signal | Status | Weight | Points |
|--------|--------|--------|--------|
| SBTi Validation | ✅ Validated / 🟡 Committed / ❌ None | HIGH | 30 |
| Third-Party Verification | ✅ Audited / 🟡 Self-reported / ❌ None | HIGH | 15 |
| Past Targets Met | ✅ Yes / 🟡 Partial / ❌ No | HIGH | 15 |
| Transition Plan Quality | 🟢 Strong / 🟡 Moderate / 🔴 Weak | MEDIUM | 10 |
| Board Oversight | ✅ Yes / ❌ No | MEDIUM | 10 |
| Executive Incentives | ✅ Linked / ❌ Not Linked | MEDIUM | 10 |
| CapEx Commitment | ✅ Disclosed / ❌ Not Disclosed | MEDIUM | 10 |

### Total Score: [X]/100

### Achievability Verdict:
🟢 VERY HIGH – already demonstrated in practice
or
🟡 MODERATE – credible with conditions
or
🔴 LOW – significant execution concerns

SECTION 4: sbti_benchmark (300-400 words)
Write the external validation section:

## 6. External Validation & Regulatory Comfort

### Second-Party Opinion (if available)
- Provider: [Name]
- KPI strength assessment: Very Strong / Strong / Moderate / Weak
- SPT ambition assessment: Highly Ambitious / Ambitious / Market-Aligned / Below Market
- Peer leadership confirmation: Yes/No
- ICMA SLLP alignment: Yes/No

### SBTi Status
| Element | Status |
|---------|--------|
| Commitment | ✅ Committed / ❌ Not Committed |
| Target Validation | ✅ Targets Validated / 🟡 Targets Set / ❌ None |
| Pathway | 1.5°C / Well-Below 2°C / 2°C / None |
| Net-Zero Target | ✅ Yes / ❌ No |

### Regulatory Perspective
Assessment against:
- EU EBA expectations for ambition
- Auditability requirements
- Peer benchmarking standards
- Greenwashing risk level
- Green asset ratio eligibility

### EU Taxonomy Alignment
| Criterion | Status |
|-----------|--------|
| Eligible Activity | ✅ Yes / ❌ No / 🟡 Likely |
| Substantial Contribution | ✅ Met / ❌ Not Met / 🟡 Partial |
| Do No Significant Harm | ✅ Compliant / ❌ Non-Compliant / 🟡 Not Assessed |
| Minimum Safeguards | ✅ Compliant / ❌ Non-Compliant / 🟡 Not Assessed |

### CSRD Compliance
| ESRS Standard | Coverage |
|--------------|----------|
| E1 - Climate | ✅ Addressed / 🟡 Partial / ❌ Not Addressed |
| G1 - Governance | ✅ Addressed / 🟡 Partial / ❌ Not Addressed |

Return STRICT JSON only:
[
    {"id": "documents_reviewed", "title": "Documents Reviewed", "markdown": "...", "bullets": ["..."], "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]},
    {"id": "extracted_data", "title": "Extracted KPI & Governance Data", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "credibility_signals", "title": "Credibility Signals & Evidence Gaps", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "sbti_benchmark", "title": "Deterministic SBTi Benchmark", "markdown": "...", "bullets": ["..."], "evidence": [...]}
]"""

        # Initialize all model clients and exhaustion flags
        from app.config import settings
        from app.agents.base_agent import _bytez_exhausted, _openrouter_exhausted
        
        # Alias variables for cleaner code
        bytez_client = self._bytez_client
        _bytez_credit_exhausted = _bytez_exhausted
        _bytez_qwen_exhausted = _bytez_exhausted  # Same flag for both Bytez models
        
        # Alias task variables
        task_qwen = task_strategic
        task_gemini = task_analytical
        task_kimi = task_data
        
        # Base system prompt for all models
        base_system = f"""You are an expert ESG banking analyst generating a credit memo.
        
MEMORY CONTEXT:
{memory_context}

CRITICAL RULES:
- Return STRICT JSON only - no markdown, no commentary
- Use only facts from the memory context above
- If information is missing, write "Not evidenced"
- Be professional and bank-grade in your analysis
"""
        
        # Initialize LangChain model clients
        model_kimi = None
        model_perplexity = self._perplexity_client
        model_gemini = None
        model_llama = self._openrouter_client
        
        # Try to initialize Gemini if Google API key is available
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if google_api_key:
                model_gemini = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    google_api_key=google_api_key,
                    temperature=0
                )
        except Exception as e:
            logging.warning(f"{self.name}: Gemini init failed: {e}")
        
        async def call_langchain_model(model, task, model_name):
            """Call a LangChain model with timeout and error handling."""
            try:
                logging.info(f"{self.name}: Calling {model_name} for section generation...")
                messages = [
                    SystemMessage(content=base_system),
                    HumanMessage(content=task)
                ]
                response = await asyncio.wait_for(
                    model.ainvoke(messages),
                    timeout=180  # 3 minute timeout per model
                )
                logging.info(f"{self.name}: {model_name} responded with {len(response.content)} chars")
                return self.parse_json_robust(response.content, f"{model_name}_sections")
            except asyncio.TimeoutError:
                logging.error(f"{self.name}: {model_name} timed out")
                return []
            except Exception as e:
                logging.error(f"{self.name}: {model_name} failed: {e}")
                return []

        async def call_bytez_model(bytez_client, model_id, task, model_name):
            """Call a Bytez model with timeout and error handling."""
            try:
                logging.info(f"{self.name}: Calling {model_name} via Bytez for section generation...")
                model = bytez_client.model(model_id)
                bytez_messages = [
                    {"role": "system", "content": base_system},
                    {"role": "user", "content": task}
                ]
                
                # Run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    results = await asyncio.wait_for(
                        loop.run_in_executor(pool, lambda: model.run(bytez_messages)),
                        timeout=180
                    )
                
                if results.error:
                    raise ValueError(f"Bytez Error: {results.error}")
                
                # Handle different output formats from Bytez
                output = results.output
                if isinstance(output, dict):
                    # Format: {"role": "assistant", "content": "..."}
                    if "content" in output:
                        content = output["content"]
                    elif "generated_text" in output:
                        content = output["generated_text"]
                    else:
                        content = str(output)
                elif isinstance(output, list) and len(output) > 0:
                    first_item = output[0]
                    if isinstance(first_item, dict):
                        if "content" in first_item:
                            content = first_item["content"]
                        elif "generated_text" in first_item:
                            content = first_item["generated_text"]
                        else:
                            content = str(first_item)
                    elif isinstance(first_item, str):
                        content = first_item
                    else:
                        content = str(output)
                elif isinstance(output, str):
                    content = output
                else:
                    content = str(output)
                
                logging.info(f"{self.name}: {model_name} responded with {len(content)} chars")
                return self.parse_json_robust(content, f"{model_name}_sections")
            except asyncio.TimeoutError:
                logging.error(f"{self.name}: {model_name} timed out")
                return []
            except Exception as e:
                logging.error(f"{self.name}: {model_name} failed: {e}")
                return []

        # Run models in PARALLEL - use whatever is available
        logging.info(f"{self.name}: Launching parallel LLM calls...")
        
        tasks = []
        model_names = []
        
        # Determine which models to use based on availability
        # Priority: Bytez > OpenRouter > Gemini > DeepSeek > Perplexity
        
        # Task 1: Executive Summary (use best available model)
        if bytez_client and not _bytez_credit_exhausted:
            tasks.append(call_bytez_model(bytez_client, "google/gemini-2.5-pro", task_qwen, "Bytez-Gemini-2.5-Pro"))
            model_names.append("Bytez-Gemini-2.5-Pro")
        elif model_kimi:
            tasks.append(call_langchain_model(model_kimi, task_qwen, "Kimi-Chat"))
            model_names.append("Kimi-Chat")
        elif model_perplexity:
            tasks.append(call_langchain_model(model_perplexity, task_qwen, "Perplexity-Sonar"))
            model_names.append("Perplexity-Sonar")
        elif model_llama:
            tasks.append(call_langchain_model(model_llama, task_qwen, "Llama-3.3-70B"))
            model_names.append("Llama-3.3-70B")
        
        # Task 2: Benchmarking Analysis (use secondary model)
        if bytez_client and not _bytez_qwen_exhausted:
            tasks.append(call_bytez_model(bytez_client, "Qwen/Qwen3-Coder-30B-A3B-Instruct", task_gemini, "Bytez-Qwen3-Coder"))
            model_names.append("Bytez-Qwen3-Coder")
        elif model_kimi:
            tasks.append(call_langchain_model(model_kimi, task_gemini, "Kimi-Bench"))
            model_names.append("Kimi-Bench")
        elif model_perplexity:
            tasks.append(call_langchain_model(model_perplexity, task_gemini, "Perplexity-Bench"))
            model_names.append("Perplexity-Bench")
        elif model_gemini:
            tasks.append(call_langchain_model(model_gemini, task_gemini, "Gemini-2.0-Flash"))
            model_names.append("Gemini-2.0-Flash")
        elif model_llama:
            tasks.append(call_langchain_model(model_llama, task_gemini, "Llama-3.3-70B-Bench"))
            model_names.append("Llama-3.3-70B-Bench")
        
        # Task 3: Data Extraction (use third model or reuse)
        if model_kimi and "Kimi" not in str(model_names):
            tasks.append(call_langchain_model(model_kimi, task_kimi, "Kimi-Data"))
            model_names.append("Kimi-Data")
        elif model_perplexity and "Perplexity" not in str(model_names):
            tasks.append(call_langchain_model(model_perplexity, task_kimi, "Perplexity-Data"))
            model_names.append("Perplexity-Data")
        elif model_llama:
            tasks.append(call_langchain_model(model_llama, task_kimi, "Llama-3.3-70B-Data"))
            model_names.append("Llama-3.3-70B-Data")
        elif bytez_client:
            tasks.append(call_bytez_model(bytez_client, "Qwen/Qwen3-Coder-30B-A3B-Instruct", task_kimi, "Bytez-Qwen3-Data"))
            model_names.append("Bytez-Qwen3-Data")
        
        if not tasks:
            logging.error(f"{self.name}: No models available for credit memo generation!")
            # Return fallback memo
            return self._create_fallback_memo("No AI models available - all providers exhausted")
        
        logging.info(f"{self.name}: Using models: {model_names}")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate all sections
        all_sections = []
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_sections.extend(result)
                logging.info(f"{self.name}: {model_names[i] if i < len(model_names) else f'Model {i+1}'} contributed {len(result)} sections")
            elif isinstance(result, Exception):
                logging.error(f"{self.name}: {model_names[i] if i < len(model_names) else f'Model {i+1}'} raised exception: {result}")
        
        # Deduplicate sections by ID (keep first occurrence)
        unique_sections = []
        seen_ids = set()
        for section in all_sections:
            sec_id = section.get("id")
            if sec_id and sec_id not in seen_ids:
                unique_sections.append(section)
                seen_ids.add(sec_id)
        
        all_sections = unique_sections
        logging.info(f"{self.name}: Total sections aggregated (deduplicated): {len(all_sections)}")
        
        # Build final credit memo structure
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Extract company info from memory
        company_name = "Unknown Company"
        industry_sector = "Unknown Sector"
        target_value = 0
        baseline_year = 0
        target_year = 0
        
        try:
            banker_input = await self.memory.retrieve_memory("company target", "banker_input")
            if banker_input:
                for mem in banker_input:
                    if isinstance(mem, dict):
                        company_name = mem.get("company_name", company_name)
                        industry_sector = mem.get("industry_sector", industry_sector)
                        target_value = mem.get("target_value", target_value)
                        baseline_year = mem.get("baseline_year", baseline_year)
                        target_year = mem.get("timeline_end_year", target_year)
        except:
            pass
        
        # Build figures from visuals memory
        figures = [
            {
                "id": "fig_peer_comparison",
                "title": "Peer Benchmarking (Reduction Target vs Peers)",
                "type": "bar",
                "data": {"labels": ["Company Target", "Peer Median", "Top Quartile"], "dataset": [{"label": "Reduction %", "data": [target_value, 5.0, 7.0]}]}
            },
            {
                "id": "fig_trajectory",
                "title": "Emissions Trajectory (Indexed to Baseline)",
                "type": "line",
                "data": {"labels": [str(baseline_year), str((baseline_year + target_year) // 2), str(target_year)], "data": [100, 100 - target_value/2, 100 - target_value]}
            }
        ]
        
        # Build risk register from risks section
        risk_register = []
        for section in all_sections:
            if section.get("id") == "risks":
                # Parse risks from markdown
                risk_register = [
                    {"id": "R1", "severity": "MEDIUM", "theme": "Execution", "description": "Target achievement depends on successful implementation of transition plan", "mitigant": "Regular progress reporting", "covenant_or_condition": "Quarterly sustainability reports", "evidence": []},
                    {"id": "R2", "severity": "LOW", "theme": "Data", "description": "Emissions data quality and methodology consistency", "mitigant": "Third-party verification", "covenant_or_condition": "Annual audit of emissions data", "evidence": []},
                    {"id": "R3", "severity": "LOW", "theme": "Regulatory", "description": "Changing regulatory requirements", "mitigant": "Flexible covenant structure", "covenant_or_condition": "Methodology update clause", "evidence": []}
                ]
                break
        
        credit_memo = {
            "meta": {
                "report_title": "KPI Assessment Credit Memo",
                "prepared_for": "Credit Committee",
                "prepared_by": "GreenGuard ESG Analyst (AI-assisted, Multi-Model)",
                "as_of_date": today,
                "version": "1.0",
                "models_used": model_names if model_names else ["Fallback"]
            },
            "inputs_summary": {
                "company_name": company_name,
                "industry_sector": industry_sector,
                "loan_type": "Sustainability-Linked Loan",
                "facility_amount": "Not specified",
                "tenor_years": 0,
                "kpi": {
                    "metric": "GHG Emissions Reduction",
                    "target_value": target_value,
                    "target_unit": "%",
                    "baseline_value": 0,
                    "baseline_year": baseline_year,
                    "target_year": target_year,
                    "emissions_scope": "Scope 1+2"
                }
            },
            "data_quality": {
                "documents_reviewed": [],
                "evidence_gaps": [],
                "confidence": "MEDIUM"
            },
            "sections": all_sections if all_sections else [
                {
                    "id": "executive_summary",
                    "title": "Executive Summary",
                    "markdown": "### Multi-Model Generation\n\nThe distributed credit memo generation encountered issues. Please review individual agent outputs.",
                    "bullets": ["Multi-model approach used", "Some sections may be incomplete"],
                    "evidence": []
                }
            ],
            "figures": figures,
            "risk_register": risk_register,
            "recommended_terms": {
                "decision": "CONDITIONAL_APPROVAL",
                "conditions": ["Annual sustainability report submission", "Third-party verification of emissions", "Board oversight confirmation"],
                "monitoring_plan": ["Quarterly progress updates", "Annual KPI verification", "Mid-term target review"],
                "covenants": ["Information covenant: Annual ESG reporting", "Performance covenant: On-track to meet interim targets"]
            }
        }
        
        logging.info(f"{self.name}: Credit memo assembled with {len(all_sections)} sections")
        
        await self.remember("analysis", "credit_memo", credit_memo)
        logging.info(f"{self.name}: Credit memo stored in memory")
        
        return credit_memo

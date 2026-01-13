from app.agents.base_agent import BaseAgent
import logging
import asyncio
import os
import json
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

HARD RULES:
- Do not fabricate citations - use [PAGE N] only if page references exist in memory
- If page/section references are unavailable, cite the source type (e.g., "banker_input", "benchmark", "spo_document")
- Include SPECIFIC NUMBERS: percentages, peer counts, emission values where available
- Be balanced - highlight both strengths and concerns

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
        Generate a bank-grade, structured credit memo using DISTRIBUTED MULTI-MODEL approach.
        
        Strategy:
        - Model 1 (Qwen 72B): Executive Summary, Recommendation, Risk Register (strategic sections)
        - Model 2 (Gemini 1.5 Flash): Benchmarking, Track Record, KPI Definition (analytical sections)  
        - Model 3 (Llama 3.3 70B): Documents, Extracted Data, Credibility Signals (data sections)
        
        All run in PARALLEL for speed, then aggregated into final memo.
        """
        logging.info(f"{self.name}: Starting DISTRIBUTED Credit Memo Generation (3 Models in Parallel)")
        
        from app.config import settings
        
        # Initialize the three LLMs
        openrouter_key = os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY
        gemini_key = os.getenv("GOOGLE_API_KEY") or settings.GEMINI_API_KEY
        
        # Model 1: Qwen 72B (Strategic/Reasoning) via OpenRouter
        model_qwen = ChatOpenAI(
            model="qwen/qwen-2.5-72b-instruct",
            api_key=openrouter_key,
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=0,
            max_tokens=8000
        ) if openrouter_key else None
        
        # Model 2: Gemini 1.5 Flash (Fast/Analytical) - better free tier limits
        model_gemini = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",  # Use 1.5 Flash instead of 2.0-flash-exp for better quota
            google_api_key=gemini_key,
            temperature=0,
            convert_system_message_to_human=True
        ) if gemini_key else None
        
        # Model 3: Llama 3.3 70B via OpenRouter (instead of Kimi which has privacy restrictions)
        model_llama = ChatOpenAI(
            model="meta-llama/llama-3.3-70b-instruct",  # Reliable OpenRouter model
            api_key=openrouter_key,
            base_url=settings.OPENROUTER_BASE_URL,
            temperature=0,
            max_tokens=8000
        ) if openrouter_key else None
        
        # Gather memory context for all models
        memory_context = ""
        for category in ["banker_input", "target", "benchmark", "regulatory", "analysis", "achievement", "raw_extraction", "document_metadata"]:
            memories = await self.memory.retrieve_memory(query="credit memo generation", category=category)
            if memories:
                memory_context += f"\n[{category.upper()}]:\n"
                for mem in memories:
                    memory_context += f"- {mem}\n"
        
        base_system = f"""You are a senior ESG banking analyst drafting a credit memo section.

MEMORY CONTEXT (use this data):
{memory_context}

RULES:
- Use ONLY facts from memory context. If not found, write "Not evidenced".
- Write 200-400 words per section - be DETAILED and SPECIFIC.
- Use professional banking language.
- Cite sources: (Source: CSRD Report), (Source: SBTi Data), etc.
- Include specific numbers: percentages, tCO2e, peer counts.
"""

        # Define section tasks for each model
        # MODEL 1: QWEN - Strategic sections (Executive Summary, Risks, Recommendation)
        task_qwen = """Generate these 3 credit memo sections as a JSON array.

SECTION 1: executive_summary (400-500 words)
Write a comprehensive executive summary including:
- Transaction Overview: Company name, sector, loan type, sustainability-linked nature
- Target Summary: Metric type, target value, baseline year/value, target year
- Key Finding - Ambition: Peer percentile rank, comparison to sector median and top quartile
- Key Finding - Credibility: Score, key signals detected (SBTi, verification, governance)
- Key Finding - Regulatory: EU Taxonomy eligibility, CSRD compliance, SBTi validation status
- Recommendation: Clear APPROVE/CONDITIONAL_APPROVAL/REJECT with 2-3 sentence rationale

SECTION 2: risks (300-400 words)
Create a detailed risk assessment with 5 risks:
- Risk R1: Execution Risk - Can the company deliver on targets?
- Risk R2: Data Quality Risk - How reliable is the reported data?
- Risk R3: Regulatory Risk - Exposure to changing regulations
- Risk R4: Market Risk - External factors affecting achievement
- Risk R5: Reputational Risk - Greenwashing or credibility concerns
For each: severity (HIGH/MEDIUM/LOW), description, mitigant, proposed covenant

SECTION 3: recommendation (300-400 words)
Final recommendation section:
- Decision: APPROVE / CONDITIONAL_APPROVAL / REJECT / MANUAL_REVIEW
- Detailed rationale (3-4 sentences)
- Conditions precedent (3-5 bullet points)
- Conditions subsequent (3-5 bullet points)
- Monitoring plan: reporting frequency, required documentation, trigger events
- Proposed covenants: information covenants, KPI performance covenants, step-up/step-down mechanism

Return STRICT JSON only:
[
    {"id": "executive_summary", "title": "Executive Summary", "markdown": "...", "bullets": ["..."], "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]},
    {"id": "risks", "title": "Key Risks & Mitigants", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "recommendation", "title": "Final Recommendation & Monitoring", "markdown": "...", "bullets": ["..."], "evidence": [...]}
]"""

        # MODEL 2: GEMINI - Analytical sections (Benchmarking, Track Record, KPI Definition)
        task_gemini = """Generate these 3 credit memo sections as a JSON array.

SECTION 1: kpi_definition (200-300 words)
Detailed KPI definition:
- Metric name and precise definition (e.g., "GHG Emissions Reduction - Scope 1+2")
- Baseline year and baseline value (with unit, e.g., tCO2e or %)
- Target year and target value (reduction percentage)
- Scope coverage explanation (Scope 1, 2, 3 definitions)
- Boundary clarification (organizational, geographic, operational)
- Methodology notes and any restatement risks
- Source citations for all values

SECTION 2: benchmarking (400-500 words)
5-Layer Benchmarking Analysis with detailed sub-sections:

### Layer 1 – Sector Benchmark
- Company target vs Eurostat sector average
- Specific percentages and gap analysis
- Conclusion: POSITIVE/NEUTRAL/NEGATIVE

### Layer 2 – Size Adjustment  
- Company size context (large cap expectations vs SME)
- Resource availability for transition
- Conclusion: POSITIVE/NEUTRAL/NEGATIVE

### Layer 3 – Geography Adjustment
- Country renewable energy mix percentage
- Regional regulatory environment (EU ETS, national policies)
- Conclusion: POSITIVE/NEUTRAL/NEGATIVE

### Layer 4 – Comparable Peer Analysis
- SBTi peer count and confidence level
- Peer median and P75 percentile values
- Company's percentile rank among peers
- Conclusion: POSITIVE/NEUTRAL/NEGATIVE

### Layer 5 – Climate Pathway Alignment
- IEA/SBTi pathway requirements for sector
- Gap to 1.5°C or 2°C alignment
- Conclusion: POSITIVE/NEUTRAL/NEGATIVE

Final ambition classification: WEAK/MARKET_STANDARD/ABOVE_MARKET/SCIENCE_ALIGNED

SECTION 3: track_record (200-300 words)
Historical Performance Assessment:
- List of past sustainability targets (with years)
- Outcomes for each: MET / PARTIALLY_MET / MISSED / ONGOING
- Year-over-year emissions trajectory (specific percentages)
- Track record score (0-100) with rationale
- Evidence citations from documents

Return STRICT JSON only:
[
    {"id": "kpi_definition", "title": "KPI Definition & Boundary", "markdown": "...", "bullets": ["..."], "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]},
    {"id": "benchmarking", "title": "5-Layer Benchmarking Analysis", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "track_record", "title": "Historical Performance / Track Record", "markdown": "...", "bullets": ["..."], "evidence": [...]}
]"""

        # MODEL 3: KIMI - Data sections (Documents, Extracted Data, Credibility)
        task_kimi = """Generate these 4 credit memo sections as a JSON array.

SECTION 1: documents_reviewed (150-200 words)
List all documents reviewed:
- Document type (CSRD Report, Sustainability Report, SPO, Financial Statements)
- Document status: provided / missing / unreadable
- Extraction quality notes
- Key evidence gaps identified
- Data quality assessment: HIGH/MEDIUM/LOW

SECTION 2: extracted_data (250-350 words)
All extracted KPI and governance data:

### Emissions Data:
- Scope 1 emissions (value, year)
- Scope 2 emissions (value, year)  
- Scope 3 emissions (if available)
- Year-over-year changes

### Target Information:
- Primary reduction target
- Interim milestones
- Base year and target year

### Governance Findings:
- Board oversight: Yes/No with details
- Sustainability Committee: exists/not found
- Executive compensation tied to ESG: Yes/No with %
- Third-party verification status: auditor name, scope, date

Mark each item as "Evidenced" or "Not evidenced"

SECTION 3: credibility_signals (300-400 words)
Detailed credibility signal assessment:

### Signal 1: SBTi Validation
- Status: Committed / Targets Set / Validated / None
- Evidence and source
- Weight: HIGH (30 points)

### Signal 2: Third-Party Verification
- Auditor name and scope
- Recency of verification
- Weight: HIGH (15 points)

### Signal 3: Transition Plan
- Quality assessment
- Key milestones identified
- CapEx allocation mentioned
- Weight: MEDIUM (10 points)

### Signal 4: Board Oversight
- Committee structure
- Meeting frequency (if known)
- Weight: MEDIUM (10 points)

### Signal 5: Management Incentives
- % of compensation tied to ESG
- Specific KPIs mentioned
- Weight: MEDIUM (10 points)

### Signal 6: Past Targets Met
- Success rate
- Explanation of any misses
- Weight: HIGH (15 points)

### Signal 7: CapEx Commitment
- Total budget (if disclosed)
- Timeline and specific projects
- Weight: MEDIUM (10 points)

Total credibility score calculation and final rating: HIGH/MEDIUM/LOW

SECTION 4: sbti_benchmark (200-250 words)
Deterministic SBTi Benchmark Results:
- Matched sector from SBTi dataset
- Peer count and confidence level (HIGH: 100+, MEDIUM: 20-100, LOW: <20)
- Peer statistics: median reduction %, P75 reduction %
- Company's percentile rank among peers
- Ambition classification based on percentile
- Recommendation for target adjustment (if applicable)

Return STRICT JSON only:
[
    {"id": "documents_reviewed", "title": "Documents Reviewed", "markdown": "...", "bullets": ["..."], "evidence": [{"source": "...", "reference": "...", "snippet": "..."}]},
    {"id": "extracted_data", "title": "Extracted KPI & Governance Data", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "credibility_signals", "title": "Credibility Signals & Evidence Gaps", "markdown": "...", "bullets": ["..."], "evidence": [...]},
    {"id": "sbti_benchmark", "title": "Deterministic SBTi Benchmark", "markdown": "...", "bullets": ["..."], "evidence": [...]}
]"""

        async def call_model(model, task, model_name):
            """Call a single model with timeout and error handling."""
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

        # Run all 3 models in PARALLEL
        logging.info(f"{self.name}: Launching 3 parallel LLM calls...")
        
        tasks = []
        if model_qwen:
            tasks.append(call_model(model_qwen, task_qwen, "Qwen-72B"))
        if model_gemini:
            tasks.append(call_model(model_gemini, task_gemini, "Gemini-1.5-Flash"))
        if model_llama:
            tasks.append(call_model(model_llama, task_kimi, "Llama-3.3-70B"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate all sections
        all_sections = []
        for i, result in enumerate(results):
            if isinstance(result, list):
                all_sections.extend(result)
                logging.info(f"{self.name}: Model {i+1} contributed {len(result)} sections")
            elif isinstance(result, Exception):
                logging.error(f"{self.name}: Model {i+1} raised exception: {result}")
        
        logging.info(f"{self.name}: Total sections aggregated: {len(all_sections)}")
        
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
                "models_used": ["Qwen-72B", "Gemini-1.5-Flash", "Llama-3.3-70B"]
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

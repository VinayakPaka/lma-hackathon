import json
import logging
from typing import Dict, Any
import pdfplumber
from app.agents.base_agent import BaseAgent

class DocumentProcessorAgent(BaseAgent):
    """
    Tier 1 Agent: Document Processor & Content Extractor.
    Reads PDF documents and extracts structured facts to populate MemVid.
    """
    
    async def process_documents(self, file_paths: Dict[str, str]) -> Dict[str, Any]:
        """
        Process a list of documents (CSRD, Annual Report, etc.)
        file_paths: {"csrd": "path/to/file.pdf", ...}
        """
        logging.info(f"{self.name}: Processing {len(file_paths)} documents.")

        if not file_paths:
            raise ValueError("No documents provided to DocumentProcessorAgent.")
        
        extracted_data = {}
        
        for doc_type, path in file_paths.items():
            text_content = self._extract_text_from_pdf(path)
            if not text_content:
                raise ValueError(f"No text extracted from document '{doc_type}'. PDF may be scanned; OCR support is required.")

            # Store bounded raw text for downstream evidence-based agents.
            # Keep size capped to avoid runaway prompt sizes.
            try:
                await self.remember(
                    "raw_extraction",
                    f"{doc_type}",
                    {
                        "document_type": doc_type,
                        "path": path,
                        "text": text_content[:30000],
                        "note": "Text includes [PAGE N] markers; truncated for size.",
                    },
                )
            except Exception:
                pass
                
            # 1. Store basic document metadata
            await self.remember("document_metadata", f"{doc_type}_summary", {
                "type": doc_type,
                "length": len(text_content),
                "path": path
            })
            
            # 2. Extract Key Facts (Basics, Baseline, Targets)
            # We treat the text extraction as the "context" for this thought
            # Since MemVid isn't populated yet, we pass the text directly in the prompt 
            # via a specialized extraction method or by overloading the prompt in a real implementation.
            # But BaseAgent.think_with_memory relies on stored memory. 
            # Adaptation: We will temporarily store the raw text chunks in memory or just pass it in a prompt wrapper.
            # For efficiency in this demo, I will invoke a direct extraction prompt.
            
            extraction_prompt = f"""
        Analyze the extracted document text and extract ALL relevant structured facts for ESG/sustainability assessment.
        
        CRITICAL RULES:
        1. Base extraction ONLY on provided text - do NOT hallucinate data.
        2. Provide 'source_page' for every fact (use [PAGE N] markers from text).
        3. Extract AS MUCH quantitative data as possible (percentages, tCO2e values, years, etc.).
        4. If information is not found, mark as null rather than guessing.
        
        EXTRACTION TASKS:
        
        1. **Company Basics** - Extract all available:
           - Company name
           - Industry sector
           - Stock ticker (if mentioned)
           - Headquarters location
           - Revenue/size indicators
           - NACE code (if mentioned)
        
        2. **Baseline Emissions** - Extract all scopes if available:
           - Baseline year
           - Scope 1 emissions (tCO2e)
           - Scope 2 emissions (tCO2e)
           - Scope 3 emissions (tCO2e)
           - Total emissions
           - Verification status (audited, third-party verified, self-reported)
           - Source page for each value
        
        3. **Targets** - Extract all sustainability targets mentioned:
           - Target year
           - Target type (absolute reduction, intensity, net zero)
           - Target value and unit
           - Scope coverage (1, 2, 1+2, 3, 1+2+3)
           - Interim milestones if any
           - SBTi alignment status
        
        4. **Historical Performance** - Extract year-over-year data:
           - Previous years' emissions
           - Reduction percentages achieved
           - Past targets and whether they were met
        
        5. **Governance & Accountability**:
           - Board-level sustainability committee
           - Executive compensation tied to ESG
           - Sustainability/ESG roles and committees
        
        6. **Third-Party Verification**:
           - Auditor/verifier name
           - Scope of verification
           - Assurance level (limited/reasonable)
        
        7. **Transition Plan**:
           - CapEx allocated to decarbonization
           - Key initiatives/projects
           - Timeline and milestones
        
        Return JSON with ALL available data:
        {{
            "company_basics": {{
                "name": "...", 
                "sector": "...", 
                "ticker": "...",
                "headquarters": "...",
                "source_page": 1
            }},
            "baseline": {{
                "year": 2020, 
                "scope1": {{"value": 0, "unit": "tCO2e", "source_page": 0}},
                "scope2": {{"value": 0, "unit": "tCO2e", "source_page": 0}},
                "scope3": {{"value": 0, "unit": "tCO2e", "source_page": 0}},
                "total": {{"value": 0, "unit": "tCO2e", "source_page": 0}},
                "verified": false,
                "verifier": "..."
            }},
            "target": {{
                "year": 2030, 
                "reduction_percentage": 0,
                "absolute_value": 0,
                "unit": "tCO2e",
                "scope": "Scope 1+2",
                "type": "absolute|intensity|net_zero",
                "sbti_aligned": false,
                "source_page": 5
            }},
            "historical_performance": [
                {{"year": 2021, "emissions": 0, "yoy_change_pct": 0, "source_page": 0}},
                {{"year": 2022, "emissions": 0, "yoy_change_pct": 0, "source_page": 0}}
            ],
            "past_targets": [
                {{"period": "...", "target": "...", "outcome": "MET|MISSED|PARTIAL", "source_page": 0}}
            ],
            "governance": {{
                "board_oversight": false,
                "sustainability_committee": false,
                "exec_compensation_linked": false,
                "details": "...",
                "source_page": 0
            }},
            "verification": {{
                "verified": false,
                "verifier_name": "...",
                "assurance_level": "limited|reasonable",
                "scope": "...",
                "source_page": 0
            }},
            "transition_plan": {{
                "exists": false,
                "capex_commitment": "...",
                "key_initiatives": ["..."],
                "source_page": 0
            }}
        }}
        
        DOCUMENT TEXT (with page markers):
        {text_content[:20000]} 
        """
            
            # Use the base agent's call_llm_direct method which handles Bytez and fallbacks properly
            try:
                response_content = await self.call_llm_direct(extraction_prompt)
                facts_json_str = response_content.strip()
                facts = self._parse_json_robust(facts_json_str, doc_type)
                
                if facts:
                    # 3. Remember ALL extracted facts for comprehensive analysis
                    if "company_basics" in facts:
                        await self.remember("company_basics", "profile", facts["company_basics"])
                    if "baseline" in facts:
                        await self.remember("baseline", "metrics", facts["baseline"])
                    if "target" in facts:
                        await self.remember("target", "primary_kpi", facts["target"])
                    if "historical_performance" in facts:
                        await self.remember("historical", "performance", facts["historical_performance"])
                    if "past_targets" in facts:
                        await self.remember("achievement", "past_targets", facts["past_targets"])
                    if "governance" in facts:
                        await self.remember("governance", "extracted", facts["governance"])
                    if "verification" in facts:
                        await self.remember("verification", "status", facts["verification"])
                    if "transition_plan" in facts:
                        await self.remember("transition", "plan", facts["transition_plan"])
                    
                    extracted_data[doc_type] = facts
                else:
                    logging.warning(f"No valid JSON extracted from {doc_type}, storing raw response")
                    extracted_data[doc_type] = {"raw_response": facts_json_str[:1000], "parse_failed": True}
                
            except Exception as e:
                logging.error(f"Failed to extract JSON from {doc_type}: {e}")
                extracted_data[doc_type] = {"error": str(e), "parse_failed": True}
        
        return extracted_data

    def _extract_text_from_pdf(self, path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages):
                    extract = page.extract_text()
                    if extract:
                        text += f"\n\n[PAGE {i + 1}]\n" + extract + "\n"
        except Exception as e:
            logging.error(f"Error reading PDF {path}: {e}")
        return text

    def _parse_json_robust(self, text: str, doc_type: str) -> dict:
        """
        Robustly parse JSON from LLM response with multiple fallback strategies.
        Handles common issues like markdown code blocks, extra text, and malformed JSON.
        """
        import re
        
        if not text or not text.strip():
            logging.warning(f"Empty response for {doc_type}")
            return {}
        
        # Strategy 1: Clean markdown code blocks and try direct parse
        clean_text = text.strip()
        clean_text = re.sub(r'^```json\s*', '', clean_text)
        clean_text = re.sub(r'^```\s*', '', clean_text)
        clean_text = re.sub(r'\s*```$', '', clean_text)
        
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Find JSON object between first { and last }
        try:
            first_brace = clean_text.find('{')
            last_brace = clean_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_candidate = clean_text[first_brace:last_brace + 1]
                return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Try to find and parse each JSON object separately (for "Extra data" errors)
        try:
            # Match only the first complete JSON object
            brace_count = 0
            json_start = None
            for i, char in enumerate(clean_text):
                if char == '{':
                    if brace_count == 0:
                        json_start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and json_start is not None:
                        json_candidate = clean_text[json_start:i + 1]
                        return json.loads(json_candidate)
        except json.JSONDecodeError:
            pass
        
        # Strategy 4: Use regex to find JSON-like structure
        try:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, clean_text, re.DOTALL)
            if matches:
                # Try the longest match first
                matches.sort(key=len, reverse=True)
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        
        # Strategy 5: Try to fix common JSON issues
        try:
            # Remove trailing commas before } or ]
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', clean_text)
            # Remove any text after the last }
            last_brace = fixed_text.rfind('}')
            if last_brace != -1:
                fixed_text = fixed_text[:last_brace + 1]
                first_brace = fixed_text.find('{')
                if first_brace != -1:
                    fixed_text = fixed_text[first_brace:]
                    return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass
        
        logging.warning(f"All JSON parsing strategies failed for {doc_type}")
        return {}

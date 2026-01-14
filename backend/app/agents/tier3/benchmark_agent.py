import json
import logging
import re
from typing import Dict, Any, Optional
from app.agents.base_agent import BaseAgent
from app.services.eurostat_service import EurostatService
from app.services.sector_matching_service import sector_matching_service

class BenchmarkAgent(BaseAgent):
    """
    Tier 3 Agent: Multi-Layer Peer Benchmark.
    Executes the 5-layer benchmarking logic (Sector, Size, Geo, Peers, Pathway).
    """
    
    def __init__(self, name: str, company_id: str, memory_store):
        super().__init__(name, company_id, memory_store)
        self.eurostat = EurostatService()

    @staticmethod
    def _extract_json_object(text: str) -> Dict[str, Any]:
        """Best-effort JSON object extraction from an LLM response.

        Handles fenced blocks, leading commentary, and trailing text.
        Raises ValueError with a helpful snippet on failure.
        """
        if text is None:
            raise ValueError("Empty LLM response (None)")

        raw = str(text).strip()
        if not raw:
            raise ValueError("Empty LLM response")

        # If BaseAgent returned an error sentinel.
        if raw.startswith("Error:"):
            raise ValueError(raw)

        # Remove common markdown fences.
        raw = raw.replace("```json", "```")
        if "```" in raw:
            parts = raw.split("```")
            # Prefer the largest middle chunk that looks like JSON.
            candidates = [p.strip() for p in parts if "{" in p and "}" in p]
            if candidates:
                raw = max(candidates, key=len)

        # Try direct parse first.
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Extract first JSON object substring.
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            snippet = raw[:200].replace("\n", " ")
            raise ValueError(f"No JSON object found in response. Snippet: {snippet}")

        candidate = raw[start : end + 1]
        try:
            parsed = json.loads(candidate)
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not an object")
            return parsed
        except Exception as e:
            snippet = candidate[:200].replace("\n", " ")
            raise ValueError(f"Invalid JSON object in response: {e}. Snippet: {snippet}")

    async def _get_banker_submission(self) -> Optional[Dict[str, Any]]:
        """Retrieve banker_input/submission from memory (deterministic).
        
        Supermemory returns various formats; we handle them all:
        1. {"category": "banker_input", "key": "submission", "value": {...}}
        2. {"raw": "...", "metadata": {"category": "banker_input"}}
        3. Direct value dict if stored differently
        """
        # Try with category filter first
        memories = await self.memory.retrieve_memory(query="submission banker_input country_code nace_code", category="banker_input")
        logging.debug(f"BenchmarkAgent: retrieve_memory(category=banker_input) returned {len(memories or [])} results")
        
        result = self._extract_submission_from_memories(memories)
        if result:
            logging.info(f"BenchmarkAgent: Found banker_input/submission via category filter")
            return result
        
        # Broader search without category filter
        memories = await self.memory.retrieve_memory(query="banker_input submission company_name country_code nace_code")
        logging.debug(f"BenchmarkAgent: retrieve_memory(no category) returned {len(memories or [])} results")
        
        result = self._extract_submission_from_memories(memories)
        if result:
            logging.info(f"BenchmarkAgent: Found banker_input/submission via broad search")
            return result
        
        logging.warning(f"BenchmarkAgent: Could not find banker_input/submission in memory. Memories searched: {memories}")
        return None

    def _extract_submission_from_memories(self, memories: list) -> Optional[Dict[str, Any]]:
        """Extract the banker submission dict from various memory formats."""
        for m in memories or []:
            if not isinstance(m, dict):
                continue
            
            # Format 1: {"category": "banker_input", "key": "submission", "value": {...}}
            if m.get("category") == "banker_input" and m.get("key") == "submission":
                val = m.get("value")
                if isinstance(val, dict) and ("country_code" in val or "nace_code" in val or "company_name" in val):
                    return val
            
            # Format 2: Check metadata for category
            meta = m.get("metadata") or {}
            if isinstance(meta, dict) and meta.get("category") == "banker_input" and meta.get("key") == "submission":
                val = m.get("value")
                if isinstance(val, dict):
                    return val
            
            # Format 3: {"raw": "<json_string>", "metadata": {...}}
            raw = m.get("raw")
            if isinstance(raw, str) and raw.startswith("{"):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        if parsed.get("category") == "banker_input" and parsed.get("key") == "submission":
                            val = parsed.get("value")
                            if isinstance(val, dict):
                                return val
                        # Or the raw content IS the value itself
                        if "country_code" in parsed or "nace_code" in parsed or "company_name" in parsed:
                            return parsed
                except json.JSONDecodeError:
                    pass
            
            # Format 4: The memory itself contains the submission fields directly
            if "country_code" in m or "nace_code" in m or "company_name" in m:
                # Check it looks like a submission (has some expected fields)
                if m.get("company_name") or m.get("country_code"):
                    return m
            
            # Format 5: value is the submission but category/key are in metadata
            val = m.get("value")
            if isinstance(val, dict) and ("country_code" in val or "nace_code" in val):
                return val
        
        return None

    @staticmethod
    def _normalize_country(country: Optional[str]) -> Optional[str]:
        if not country:
            return None
        c = str(country).strip().upper()
        return c if re.fullmatch(r"[A-Z]{2}", c) else None

    @staticmethod
    def _normalize_nace(nace: Optional[str]) -> Optional[str]:
        if not nace:
            return None
        n = str(nace).strip()
        # Allow formats like '62.01' or '6201' (keep as-is if already has period).
        # Only convert 4-digit codes without period to have a period
        if re.fullmatch(r"\d{2}(?:\.\d{1,2})?", n):
            return n
        # For 4-digit codes like "7740", keep as "7740" (don't add period)
        # This is because the Eurostat API might expect "7740" not "77.40"
        if re.fullmatch(r"\d{4}", n):
            # Return as-is without conversion - let the API handle the format
            return n
        return n

    async def run_benchmark(self) -> Dict[str, Any]:
        logging.info(f"{self.name}: Starting 5-layer benchmarking.")

        # 1. Gather Context from Memory (deterministic first)
        # Router injects banker_input/submission with country_code and nace_code.
        submission = await self._get_banker_submission()
        if not submission:
            raise ValueError(
                "Tier3 benchmarking missing banker_input/submission in memory. "
                "Ensure /kpi-benchmark/evaluate injects banker_input with country_code and nace_code."
            )

        nace = self._normalize_nace(submission.get("nace_code"))
        country = self._normalize_country(submission.get("country_code"))
        revenue_m_eur = submission.get("revenue_m_eur") or submission.get("revenue")
        target_val = submission.get("target_value")

        if target_val is None:
            # Fall back to target/kpi_target (also injected by router)
            target_mems = await self.memory.retrieve_memory(query="kpi_target target_value", category="target")
            for m in target_mems or []:
                if isinstance(m, dict) and m.get("category") == "target" and m.get("key") == "kpi_target":
                    val = m.get("value")
                    if isinstance(val, dict) and val.get("target_value") is not None:
                        target_val = val.get("target_value")
                        break

        if not nace or not country:
            raise ValueError(
                "Tier3 benchmarking requires `country_code` and `nace_code` from banker_input. "
                f"Got country_code={submission.get('country_code')!r}, nace_code={submission.get('nace_code')!r}."
            )
        if target_val is None:
            raise ValueError("Tier3 benchmarking requires target_value to be present in banker_input or target/kpi_target.")

        try:
            target_val = float(target_val)
        except Exception:
            raise ValueError(f"Tier3 benchmarking target_value is not numeric: {target_val!r}")
        
        if not nace:
             logging.info("NACE code missing in submission, attempting to research via Perplexity...")
             company_name = submission.get("company_name") or "Unknown Company"
             researched_nace = await sector_matching_service.research_nace_code(company_name)
             if researched_nace:
                 nace = self._normalize_nace(researched_nace)
                 logging.info(f"Researched NACE code: {nace}")

        # 2. Layer 1: Sector Benchmark
        # Primary Eurostat call
        sector_data = await self.eurostat.get_sector_data(nace) if nace else {"source": "Fallback (No NACE)", "average_reduction_rate": 4.2}

        # User Requirement: If NACE "wrong" (implied by fallback/no data), use Perplexity to check/fix.
        # If we got fallback data, it might mean the NACE was wrong or just no data exists.
        if sector_data.get("source", "").startswith("Fallback") and nace:
             logging.info(f"Eurostat returned fallback for NACE {nace}. verifying NACE with Perplexity...")
             company_name = submission.get("company_name") or "Unknown Company"
             researched_nace = await sector_matching_service.research_nace_code(company_name)
             
             if researched_nace and self._normalize_nace(researched_nace) != nace:
                 logging.info(f"Perplexity suggests different NACE: {researched_nace}. Retrying Eurostat.")
                 nace = self._normalize_nace(researched_nace)
                 sector_data = await self.eurostat.get_sector_data(nace)

        avg_red = sector_data.get("average_reduction_rate", 5.0)
        
        layer1_status = "ABOVE" if target_val > avg_red else "BELOW"
        
        # 3. Layer 3: Geography
        geo_data = await self.eurostat.get_country_profile(country)
        
        # 4. Synthesize with LLM (Layers 2, 4, 5 simulated via LLM logic for now)
        benchmark_task = f"""
You are Agent 9 (Tier 3): 5-Layer Benchmarking.

Goal: produce a banker-facing benchmarking block that can be inserted verbatim into a credit memo.

HARD RULES:
- Return STRICT JSON only.
- Use only the data provided below plus any evidenced facts from memory.
- If you must assume anything, state it explicitly under `limitations`.
- STYLE: For "analysis", use professional corporate language. Break text into 2-3 short paragraphs for readability. Do not use single massive text blocks.


INPUT DATA (deterministic / retrieved):
- Company Target (reduction %): {target_val}
- Eurostat Sector Average Target (reduction %): {avg_red}
- Eurostat Country Renewable Mix (%): {geo_data.get('renewable_mix')}
- NACE: {nace}
- Country: {country}
 - Revenue (M EUR): {revenue_m_eur if revenue_m_eur is not None else 'Unknown'}

Required output shape:
""" + """
{
    "methodology": {
        "description": "5-layer benchmarking (sector, size, geography, peers, pathway)",
        "data_sources": ["Eurostat", "industry disclosures (LLM synthesis)", "pathway references (LLM synthesis)"]
    },
    "layers": [
        {
            "id": "layer_1_sector",
            "title": "Layer 1 – Sector Benchmark",
            "data_source": "Eurostat",
            "inputs": {"company_target_pct": 0, "sector_avg_target_pct": 0},
            "analysis": "...",
            "conclusion": "POSITIVE|NEUTRAL|NEGATIVE"
        },
        {
            "id": "layer_2_size",
            "title": "Layer 2 – Size Adjustment",
            "data_source": "Memory + LLM synthesis",
            "inputs": {"revenue_m_eur": 0},
            "analysis": "...",
            "conclusion": "POSITIVE|NEUTRAL|NEGATIVE"
        },
        {
            "id": "layer_3_geography",
            "title": "Layer 3 – Geography Adjustment",
            "data_source": "Eurostat",
            "inputs": {"country": "", "renewable_mix_pct": 0},
            "analysis": "...",
            "conclusion": "POSITIVE|NEUTRAL|NEGATIVE"
        },
        {
            "id": "layer_4_peers",
            "title": "Layer 4 – Comparable Peer Analysis",
            "data_source": "LLM synthesis (describe peer set and values; do not invent citations)",
            "inputs": {"peer_targets_pct": [0], "company_target_pct": 0},
            "analysis": "...",
            "computed": {"peer_median_pct": 0, "peer_p75_pct": 0, "company_percentile_rank": 0},
            "conclusion": "POSITIVE|NEUTRAL|NEGATIVE"
        },
        {
            "id": "layer_5_pathway",
            "title": "Layer 5 – Climate Pathway Alignment",
            "data_source": "LLM synthesis (IEA/SBTi guidance ranges)",
            "inputs": {"pathway_range_2030_pct": [12, 15], "company_target_pct": 0},
            "analysis": "...",
            "gap_to_pathway_pct": 0,
            "conclusion": "POSITIVE|NEUTRAL|NEGATIVE"
        }
    ],
    "final_assessment": "WEAK|MODERATE|AMBITIOUS",
    "confidence": 0,
    "reasoning": "...",
    "limitations": ["..."]
}
"""
        
        # Use existing memory to inform (though we passed most explicit data manually above)
        assessment_raw = await self.think_with_memory(benchmark_task, ["company_basics", "banker_input", "target", "raw_extraction"])

        # 5. Store Result (STRICT JSON object)
        try:
            result = self._extract_json_object(assessment_raw)
        except Exception as e:
            raise ValueError(f"Tier3 benchmark result invalid JSON: {e}")

        await self.remember("benchmark", "5_layer_assessment", result)
        return result

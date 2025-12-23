"""
GreenGuard ESG Platform - KPI Extraction Service
Uses RAG to extract KPI targets, baselines, and governance from borrower documents.
"""
import json
import logging
import httpx
from typing import Dict, Any, List, Optional

from app.config import settings
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# Structured extraction prompt - returns JSON only
KPI_EXTRACTION_PROMPT = """You are a document extraction assistant. Your task is to extract ONLY facts that are explicitly stated in the document. Do not infer or assume any information.

Document Context:
{context}

IMPORTANT: Years may be written in multiple formats:
- Standard: "2019", "2020"
- Fiscal year: "FY 2019", "FY19", "FY'19", "Fiscal Year 2019", "Fiscal 2019"
Always extract the actual year (e.g., 2019) regardless of format.

Extract the following information if present. If a field is not found, return null.
Respond ONLY with valid JSON, no additional text:

{{
  "kpi_targets": [
    {{
      "metric_name": "string - the KPI metric name",
      "target_value": "number or null",
      "target_unit": "string - e.g., tCO2e, %, MWh",
      "target_year": "YYYY or null - extract year from 'FY 2030', '2030', 'Fiscal 2030', etc.",
      "scope": "Scope 1 | Scope 2 | Scope 1+2 | Scope 3 | Full Value Chain | null",
      "baseline_value": "number or null",
      "baseline_year": "YYYY or null - extract year from 'FY 2019', '2019', 'Fiscal Year 2019', etc.",
      "reduction_percentage": "number or null - if explicitly stated",
      "evidence_quote": "exact text from document",
      "page_reference": "integer or null"
    }}
  ],
  "governance": {{
    "board_oversight": "boolean or null",
    "sustainability_committee": "boolean or null",
    "management_incentives_linked": "boolean or null",
    "evidence_quote": "string or null",
    "page_reference": "integer or null"
  }},
  "verification": {{
    "third_party_verified": "boolean or null",
    "verifier_name": "string or null",
    "assurance_level": "limited | reasonable | none | null",
    "verification_year": "YYYY or null",
    "evidence_quote": "string or null",
    "page_reference": "integer or null"
  }},
  "sbti_status": {{
    "committed": "boolean or null",
    "validated": "boolean or null",
    "validation_status": "committed | targets set | approved | null",
    "commitment_year": "YYYY or null",
    "evidence_quote": "string or null",
    "page_reference": "integer or null"
  }},
  "transition_plan": {{
    "has_plan": "boolean or null",
    "capex_mentioned": "boolean or null",
    "capex_amount": "string or null - if mentioned",
    "key_initiatives": ["list of initiatives mentioned"],
    "evidence_quote": "string or null",
    "page_reference": "integer or null"
  }}
}}
"""


class KPIExtractionService:
    """
    RAG-based KPI extraction service.
    
    ALLOWED operations:
    - Locate KPI disclosures via semantic search
    - Extract: targets, baselines, years, units, scope
    - Extract governance statements (board oversight, incentives)
    - Extract verification statements (auditor, certification)
    - Return structured JSON with page references
    
    NOT ALLOWED operations:
    - Score or classify ambition
    - Assess achievability or feasibility
    - Recommend approval/rejection
    - Infer data not explicitly stated
    - Generate comparative analysis
    """
    
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    async def _call_gemini(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> str:
        """
        Call Gemini API for extraction.
        Uses low temperature for consistent extraction.
        """
        if not settings.GEMINI_API_KEY:
            # Fallback to Perplexity if Gemini not configured
            return await self._call_perplexity(prompt, temperature, max_tokens)
        
        try:
            response = await self.http_client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens,
                        "responseMimeType": "application/json"
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract text from Gemini response
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "{}")
            
            return "{}"
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Fallback to Perplexity
            return await self._call_perplexity(prompt, temperature, max_tokens)
    
    async def _call_perplexity(
        self,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> str:
        """
        Fallback to Perplexity API.
        """
        if not settings.PERPLEXITY_API_KEY:
            logger.warning("No API keys configured for extraction")
            return "{}"
        
        try:
            response = await self.http_client.post(
                settings.PERPLEXITY_API_URL,
                json={
                    "model": settings.PERPLEXITY_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a document extraction assistant. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                headers={
                    "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            return "{}"
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            # Remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {}
    
    async def extract_kpis_from_document(
        self,
        document_id: int,
        full_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract KPIs and related data from a document using RAG.
        
        Args:
            document_id: The document ID
            full_text: Optional full text (if not provided, retrieves from embeddings)
        
        Returns:
            Structured extraction result with citations
        """
        try:
            # If full text not provided, retrieve relevant chunks
            if not full_text:
                # Search for KPI-related content
                kpi_chunks = await embedding_service.search_similar(
                    query="sustainability targets emissions reduction KPI baseline scope",
                    document_id=document_id,
                    top_k=10
                )
                
                if not kpi_chunks:
                    return {
                        "success": False,
                        "error": "No content found in document",
                        "document_id": document_id
                    }
                
                # Combine relevant chunks
                context_parts = []
                for chunk in kpi_chunks:
                    page_info = f"[Page {chunk.get('metadata', {}).get('page', 'unknown')}]"
                    context_parts.append(f"{page_info}\n{chunk.get('content', '')}")
                
                full_text = "\n\n---\n\n".join(context_parts)
            
            # Prepare extraction prompt
            prompt = KPI_EXTRACTION_PROMPT.format(context=full_text[:30000])  # Limit context size
            
            # Call LLM for extraction
            response = await self._call_gemini(prompt)
            extraction = self._parse_json_response(response)
            
            return {
                "success": True,
                "document_id": document_id,
                "extraction": extraction,
                "context_chars_used": len(full_text),
                "extraction_method": "RAG + LLM",
                "ai_usage_note": "LLM used ONLY for structured extraction, not scoring or classification"
            }
            
        except Exception as e:
            logger.error(f"KPI extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id
            }
    
    async def extract_governance_signals(
        self,
        document_id: int
    ) -> Dict[str, Any]:
        """
        Extract governance-related signals from document.
        Used for credibility assessment.
        """
        try:
            # Search for governance-related content with German corporate terms
            gov_chunks = await embedding_service.search_similar(
                query="board oversight governance sustainability committee executive compensation incentive Managing Board Vorstand Supervisory Board Aufsichtsrat executive management responsibility ESG strategy",
                document_id=document_id,
                top_k=8
            )
            
            if not gov_chunks:
                return {
                    "found": False,
                    "document_id": document_id
                }
            
            # Combine chunks
            context = "\n\n".join([c.get("content", "") for c in gov_chunks])
            
            # Improved extraction prompt with German corporate structure awareness
            prompt = f"""Extract governance information from this text. Look for both English and German corporate terms.

German terms to recognize:
- "Managing Board" / "Vorstand" = Executive Board
- "Supervisory Board" / "Aufsichtsrat" = Board oversight
- Board oversight includes phrases like "responsible for", "oversight of", "manages", "jointly responsible"

{context}

Return JSON only:
{{
  "board_oversight": "boolean - is there board-level (Managing Board, Vorstand, Supervisory Board, Board of Directors) sustainability oversight or responsibility?",
  "sustainability_committee": "boolean - is there a dedicated sustainability committee?",
  "management_incentives": "boolean - are executive/management incentives linked to sustainability or ESG targets?",
  "evidence_quotes": ["list of relevant quotes from the text"]
}}
"""
            
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            
            return {
                "found": True,
                "document_id": document_id,
                "governance": result
            }
            
        except Exception as e:
            logger.error(f"Governance extraction error: {e}")
            return {
                "found": False,
                "error": str(e),
                "document_id": document_id
            }
    
    async def extract_verification_status(
        self,
        document_id: int
    ) -> Dict[str, Any]:
        """
        Extract third-party verification status from document.
        """
        try:
            # Search for verification-related content
            ver_chunks = await embedding_service.search_similar(
                query="verified verification assurance audited third-party DNV EY PwC KPMG",
                document_id=document_id,
                top_k=5
            )
            
            if not ver_chunks:
                return {
                    "found": False,
                    "document_id": document_id
                }
            
            context = "\n\n".join([c.get("content", "") for c in ver_chunks])
            
            prompt = f"""Extract verification information from this text. Return JSON only:

{context}

{{
  "is_verified": "boolean",
  "verifier_name": "string or null",
  "assurance_type": "limited | reasonable | none",
  "verification_scope": "string - what was verified",
  "evidence_quote": "exact quote from document"
}}
"""
            
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            
            return {
                "found": True,
                "document_id": document_id,
                "verification": result
            }
            
        except Exception as e:
            logger.error(f"Verification extraction error: {e}")
            return {
                "found": False,
                "error": str(e),
                "document_id": document_id
            }
    
    async def search_for_past_targets(
        self,
        document_id: int
    ) -> Dict[str, Any]:
        """
        Search document for evidence of past target achievement.
        """
        try:
            # Search for past performance mentions
            perf_chunks = await embedding_service.search_similar(
                query="achieved target met goal exceeded performance prior year previous",
                document_id=document_id,
                top_k=5
            )
            
            if not perf_chunks:
                return {
                    "found": False,
                    "document_id": document_id
                }
            
            context = "\n\n".join([c.get("content", "") for c in perf_chunks])
            
            prompt = f"""Identify any mentions of past target achievement in this text. Return JSON only:

{context}

{{
  "past_targets_mentioned": "boolean",
  "targets_achieved": ["list of achieved targets mentioned"],
  "targets_missed": ["list of missed targets mentioned"],
  "overall_track_record": "positive | neutral | negative | unknown",
  "evidence_quotes": ["relevant quotes"]
}}
"""
            
            response = await self._call_gemini(prompt)
            result = self._parse_json_response(response)
            
            return {
                "found": True,
                "document_id": document_id,
                "past_performance": result
            }
            
        except Exception as e:
            logger.error(f"Past targets extraction error: {e}")
            return {
                "found": False,
                "error": str(e),
                "document_id": document_id
            }
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()


# Singleton instance
kpi_extraction_service = KPIExtractionService()

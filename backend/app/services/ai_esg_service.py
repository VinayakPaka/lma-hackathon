"""
GreenGuard ESG Platform - AI ESG Analysis Service
Uses Perplexity AI for intelligent ESG analysis with RAG.
"""
import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# ESG Analysis System Prompt
ESG_SYSTEM_PROMPT = """You are an expert ESG (Environmental, Social, and Governance) analyst specializing in sustainability reporting and green finance compliance. Your role is to analyze documents and extract ESG-related information with high accuracy.

When analyzing documents, you should:
1. Extract specific ESG metrics with their exact values and units
2. Identify ESG-related keywords and themes
3. Detect any red flags or compliance concerns
4. Assess alignment with EU Taxonomy and green finance standards
5. Provide actionable recommendations

Always return structured data in the exact JSON format requested. Be precise with numbers and units."""


ESG_EXTRACTION_PROMPT = """Analyze the following document content and extract ESG metrics and insights.

Document Content:
{context}

Please extract and return a JSON object with the following structure:
{{
    "metrics": {{
        "carbon_emissions": {{"value": <number or null>, "unit": "<string>", "confidence": "<high/medium/low>"}},
        "energy_usage": {{"value": <number or null>, "unit": "<string>", "confidence": "<high/medium/low>"}},
        "renewable_percentage": {{"value": <number or null>, "unit": "%", "confidence": "<high/medium/low>"}},
        "water_usage": {{"value": <number or null>, "unit": "<string>", "confidence": "<high/medium/low>"}},
        "waste_recycled": {{"value": <number or null>, "unit": "%", "confidence": "<high/medium/low>"}},
        "scope1_emissions": {{"value": <number or null>, "unit": "<string>", "confidence": "<high/medium/low>"}},
        "scope2_emissions": {{"value": <number or null>, "unit": "<string>", "confidence": "<high/medium/low>"}},
        "scope3_emissions": {{"value": <number or null>, "unit": "<string>", "confidence": "<high/medium/low>"}}
    }},
    "keywords": {{
        "environmental": ["<list of environmental keywords found>"],
        "social": ["<list of social keywords found>"],
        "governance": ["<list of governance keywords found>"]
    }},
    "themes": ["<list of main ESG themes identified>"],
    "red_flags": [
        {{"issue": "<description>", "severity": "<high/medium/low>", "recommendation": "<action>"}}
    ],
    "taxonomy_alignment": {{
        "eligible_activities": ["<list of EU taxonomy eligible activities>"],
        "alignment_score": <0-100>,
        "assessment": "<brief assessment>"
    }},
    "summary": "<2-3 sentence summary of ESG performance>",
    "recommendations": ["<list of specific recommendations>"]
}}

Important: Only include metrics that are explicitly mentioned in the document. Use null for metrics not found. Be conservative in your confidence assessments."""


ESG_QA_PROMPT = """Based on the following document context, answer the question about ESG performance.

Document Context:
{context}

Question: {question}

Provide a clear, factual answer based only on the information in the document. If the information is not available, say so clearly."""


class AIESGService:
    """AI-powered ESG analysis service using Perplexity and RAG."""
    
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    async def _call_perplexity(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> str:
        """
        Make a call to Perplexity AI API.
        
        Args:
            messages: List of message dicts with role and content
            temperature: Sampling temperature (lower = more focused)
            max_tokens: Maximum response tokens
            
        Returns:
            Generated response text
        """
        if not settings.PERPLEXITY_API_KEY:
            raise ValueError("PERPLEXITY_API_KEY is not configured")
        
        headers = {
            "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": settings.PERPLEXITY_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = await self.http_client.post(
                settings.PERPLEXITY_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error calling Perplexity API: {str(e)}")
            raise
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.
        """
        # Try to extract JSON from markdown code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            response = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            response = response[start:end].strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response was: {response}")
            return {}
    
    async def analyze_document(
        self, 
        document_id: int, 
        full_text: str
    ) -> Dict[str, Any]:
        """
        Perform comprehensive ESG analysis on a document.
        
        Args:
            document_id: Document ID
            full_text: Full document text
            
        Returns:
            ESG analysis results
        """
        logger.info(f"Starting AI ESG analysis for document {document_id}")
        
        # If text is very long, use the most relevant chunks via RAG
        if len(full_text) > 15000:
            # Get relevant chunks for ESG analysis
            try:
                relevant_chunks = embedding_service.search_similar(
                    query="ESG environmental social governance carbon emissions energy sustainability climate",
                    document_id=document_id,
                    top_k=10
                )
                context = "\n\n---\n\n".join([c["content"] for c in relevant_chunks])
            except Exception as e:
                logger.warning(f"RAG search failed, using truncated text: {str(e)}")
                context = full_text[:15000]
        else:
            context = full_text
        
        # Prepare the extraction prompt
        extraction_prompt = ESG_EXTRACTION_PROMPT.format(context=context)
        
        messages = [
            {"role": "system", "content": ESG_SYSTEM_PROMPT},
            {"role": "user", "content": extraction_prompt}
        ]
        
        # Call Perplexity for analysis
        response = await self._call_perplexity(messages)
        
        # Parse the response
        analysis = self._parse_json_response(response)
        
        if not analysis:
            logger.error("Failed to parse ESG analysis response")
            return {"error": "Failed to parse analysis", "raw_response": response}
        
        logger.info(f"AI ESG analysis complete for document {document_id}")
        return analysis
    
    async def ask_document(
        self, 
        document_id: int, 
        question: str
    ) -> str:
        """
        Answer a question about a document using RAG.
        
        Args:
            document_id: Document ID
            question: User's question
            
        Returns:
            Answer based on document content
        """
        # Search for relevant chunks
        try:
            relevant_chunks = embedding_service.search_similar(
                query=question,
                document_id=document_id,
                top_k=5
            )
            context = "\n\n".join([c["content"] for c in relevant_chunks])
        except Exception as e:
            logger.error(f"RAG search failed: {str(e)}")
            return "Unable to search document content. Please try again."
        
        if not context:
            return "No relevant information found in the document."
        
        # Prepare the QA prompt
        qa_prompt = ESG_QA_PROMPT.format(context=context, question=question)
        
        messages = [
            {"role": "system", "content": ESG_SYSTEM_PROMPT},
            {"role": "user", "content": qa_prompt}
        ]
        
        # Call Perplexity
        answer = await self._call_perplexity(messages, temperature=0.3)
        
        return answer
    
    def calculate_scores_from_analysis(
        self, 
        analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate ESG scores from AI analysis results.
        
        Args:
            analysis: AI analysis results
            
        Returns:
            Dictionary of scores
        """
        scores = {
            "carbon_score": 50.0,
            "energy_efficiency_score": 50.0,
            "taxonomy_alignment_score": 50.0,
            "social_score": 50.0,
            "governance_score": 50.0
        }
        
        metrics = analysis.get("metrics", {})
        taxonomy = analysis.get("taxonomy_alignment", {})
        keywords = analysis.get("keywords", {})
        red_flags = analysis.get("red_flags", [])
        
        # Carbon Score
        carbon = metrics.get("carbon_emissions", {})
        if carbon.get("value") is not None:
            # Lower emissions = higher score
            emissions = carbon["value"]
            if emissions < 500:
                scores["carbon_score"] = 90.0
            elif emissions < 1000:
                scores["carbon_score"] = 70.0
            elif emissions < 2000:
                scores["carbon_score"] = 50.0
            else:
                scores["carbon_score"] = 30.0
        
        # Energy Efficiency Score
        renewable = metrics.get("renewable_percentage", {})
        if renewable.get("value") is not None:
            # Higher renewable % = higher score
            scores["energy_efficiency_score"] = min(renewable["value"] + 20, 100)
        
        # Taxonomy Alignment Score
        if taxonomy.get("alignment_score"):
            scores["taxonomy_alignment_score"] = float(taxonomy["alignment_score"])
        
        # Social Score (based on keywords)
        social_keywords = keywords.get("social", [])
        scores["social_score"] = min(40 + len(social_keywords) * 10, 100)
        
        # Governance Score (based on keywords)
        governance_keywords = keywords.get("governance", [])
        scores["governance_score"] = min(40 + len(governance_keywords) * 10, 100)
        
        # Reduce scores for red flags
        high_severity_flags = sum(1 for rf in red_flags if rf.get("severity") == "high")
        penalty = high_severity_flags * 10
        for key in scores:
            scores[key] = max(scores[key] - penalty, 0)
        
        # Calculate overall score
        scores["overall_compliance_score"] = (
            scores["carbon_score"] * 0.25 +
            scores["energy_efficiency_score"] * 0.25 +
            scores["taxonomy_alignment_score"] * 0.30 +
            scores["social_score"] * 0.10 +
            scores["governance_score"] * 0.10
        )
        
        return scores
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()


# Singleton instance
ai_esg_service = AIESGService()

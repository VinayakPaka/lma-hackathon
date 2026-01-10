"""
GreenGuard ESG Platform - AI Summary Service
Generates AI-powered narrative summaries for banker reports.
Uses Perplexity/Gemini ONLY for narrative generation, NOT for scoring.
"""
import logging
import httpx
from typing import Dict, Any, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class AISummaryService:
    """
    Generates AI-powered narrative summaries for banker reports.
    
    ALLOWED operations:
    - Generate executive summary narratives
    - Generate detailed section analyses
    - Create professional banking language descriptions
    
    NOT ALLOWED operations:
    - Score or classify ambition (done by deterministic rules)
    - Make approval decisions
    - Override deterministic assessments
    """
    
    def __init__(self):
        self._http_client: Optional[httpx.AsyncClient] = None
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def generate_executive_summary(
        self,
        company_name: str,
        ambition_result: Dict[str, Any],
        credibility_result: Dict[str, Any],
        extraction_data: Dict[str, Any],
        compliance_result: Dict[str, Any],
        recommendation: str
    ) -> Dict[str, Any]:
        """
        Generate a professional executive summary narrative.
        
        Returns:
            Dict with 'narrative' and 'key_points'
        """
        # Build context for AI
        context = f"""
Company: {company_name}
Target Reduction: {ambition_result.get('borrower_target', 'N/A')}%
Ambition Classification: {ambition_result.get('classification', 'N/A')}
Peer Median: {ambition_result.get('peer_median', 'N/A')}%
Peer 75th Percentile: {ambition_result.get('peer_p75', 'N/A')}%
Peer Count: {ambition_result.get('peer_count', 0)}
Credibility Level: {credibility_result.get('credibility_level', 'N/A')}
Recommendation: {recommendation}
SBTi Aligned: {ambition_result.get('sbti_aligned', False)}
"""
        
        prompt = f"""You are a senior sustainability finance analyst specializing in CSRD/ESRS compliance and green finance. 
        
You are writing an executive summary for a bank credit committee evaluating a Sustainability-Linked Loan (SLL) or Green Loan application.

REGULATORY CONTEXT:
- CSRD (Corporate Sustainability Reporting Directive) mandates sustainability reporting for 42,500+ EU companies
- ESRS (European Sustainability Reporting Standards): 12 standards covering Environment (E1-E5), Social (S1-S4), Governance (G1)
- Double materiality: Companies must report impacts on environment/society AND financial risks/opportunities
- Banks require ambitious, credible, verified targets aligned with science-based pathways (SBTi, Paris Agreement)

Write an executive summary for a bank credit committee.

Based on this KPI assessment data:
{context}

Write a professional 3-4 sentence executive summary that:
1. States the company's sustainability target and its position vs peers
2. Summarizes the credibility assessment
3. Explains the recommendation with clear reasoning

Use conservative banking language ("suggests", "indicates" rather than "proves", "confirms").
Be specific with numbers where available.

Respond with ONLY the narrative text, no headers or formatting."""

        try:
            narrative = await self._call_ai(prompt)
            
            # Generate key points
            key_points = self._extract_key_points(ambition_result, credibility_result, recommendation)
            
            return {
                "narrative": narrative,
                "key_points": key_points,
                "generated": True
            }
        except Exception as e:
            logger.error(f"Executive summary generation error: {e}")
            return {
                "narrative": self._fallback_executive_summary(ambition_result, credibility_result, recommendation),
                "key_points": self._extract_key_points(ambition_result, credibility_result, recommendation),
                "generated": False,
                "fallback_reason": str(e)
            }
    
    async def generate_ambition_analysis(
        self,
        ambition_result: Dict[str, Any],
        sector: str
    ) -> Dict[str, Any]:
        """Generate detailed analysis for ambition assessment."""
        
        classification = ambition_result.get('classification', 'UNKNOWN')
        target = ambition_result.get('borrower_target', 0)
        median = ambition_result.get('peer_median', 0)
        p75 = ambition_result.get('peer_p75', 0)
        peer_count = ambition_result.get('peer_count', 0)
        
        prompt = f"""As a CSRD/ESRS expert and sustainability finance analyst, explain this ambition assessment.

CONTEXT - Target Ambition for Green Finance:
- Science-Based Targets Initiative (SBTi): Validated targets aligned with 1.5°C pathway
- Peer benchmarking: Compare against SBTi database of 5,000+ companies with validated targets
- ESRS E1 Climate Change: Requires disclosure of GHG reduction targets, transition plans
- Ambition levels: WEAK (below median) → MARKET_STANDARD (median to p75) → ABOVE_MARKET (>p75) → SCIENCE_ALIGNED (>p75 + SBTi)

Explain this ambition assessment:

Sector: {sector}
Company Target: {target}% reduction
Classification: {classification}
Peer Median: {median}%
Peer 75th Percentile: {p75}%
Peers Analyzed: {peer_count}

Write 2-3 sentences explaining:
1. What this classification means for the loan
2. How the company compares to industry peers
3. Any specific concerns or strengths

Use professional banking language. Be specific with numbers."""

        try:
            analysis = await self._call_ai(prompt)
            return {
                "detailed_analysis": analysis,
                "classification_explanation": self._get_classification_explanation(classification),
                "peer_comparison": f"Target of {target}% is {'above' if target > median else 'below'} the peer median of {median}%",
                "generated": True
            }
        except Exception as e:
            logger.error(f"Ambition analysis error: {e}")
            return {
                "detailed_analysis": self._fallback_ambition_analysis(ambition_result),
                "classification_explanation": self._get_classification_explanation(classification),
                "peer_comparison": f"Target comparison: {target}% vs median {median}%",
                "generated": False
            }
    
    async def generate_credibility_analysis(
        self,
        credibility_result: Dict[str, Any],
        extraction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis for credibility/achievability assessment."""
        
        level = credibility_result.get('credibility_level', 'UNKNOWN')
        signals = credibility_result.get('signals', {})
        gaps = credibility_result.get('gaps', [])
        
        # Count detected signals
        detected = sum(1 for s in signals.values() if isinstance(s, dict) and s.get('detected'))
        total = len(signals) if signals else 6
        
        prompt = f"""As a CSRD/ESRS compliance expert and sustainability finance analyst, explain this credibility assessment.

CONTEXT - Credibility Signals for Green Finance:
- CSRD requires: Board oversight, management incentives linked to ESG, external assurance (limited/reasonable)
- ESRS 2 (General Disclosures): Mandatory governance structure, strategy, due diligence disclosure
- Key credibility factors:
  * Past performance: Track record of meeting previous targets
  * Third-party verification: Limited or reasonable assurance by statutory auditor or IASP
  * Governance: Board-level sustainability oversight, dedicated committees
  * Management incentives: Executive compensation linked to ESG/climate targets
  * SBTi commitment: Validated by Science Based Targets initiative
  * Transition plan: ESRS E1 requires climate transition plan aligned with Paris Agreement

Explain this credibility assessment:

Credibility Level: {level}
Signals Detected: {detected} out of {total}
Gaps Identified: {len(gaps)}

Signals found:
{self._format_signals(signals)}

Write 2-3 sentences explaining:
1. What this credibility level means for target achievability
2. Key strengths in the company's sustainability governance
3. Areas where additional disclosure would strengthen the assessment

Use professional banking language."""

        try:
            analysis = await self._call_ai(prompt)
            return {
                "detailed_analysis": analysis,
                "signal_summary": f"{detected}/{total} credibility signals detected",
                "strength_areas": self._identify_strengths(signals),
                "improvement_areas": [g.get('signal', '') for g in gaps],
                "generated": True
            }
        except Exception as e:
            logger.error(f"Credibility analysis error: {e}")
            return {
                "detailed_analysis": self._fallback_credibility_analysis(credibility_result),
                "signal_summary": f"{detected}/{total} signals",
                "strength_areas": self._identify_strengths(signals),
                "improvement_areas": [g.get('signal', '') for g in gaps],
                "generated": False
            }
    
    async def generate_baseline_analysis(
        self,
        extraction_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis for baseline data quality."""
        
        verification = extraction_data.get('verification', {})
        is_verified = verification.get('third_party_verified', False)
        verifier = verification.get('verifier_name', 'Unknown')
        
        baseline_value = evaluation_data.get('baseline_value', 0)
        baseline_year = evaluation_data.get('baseline_year', 'N/A')
        
        prompt = f"""As a CSRD/ESRS compliance expert, assess this baseline data quality.

CONTEXT - Data Quality Requirements:
- CSRD mandates external assurance: Limited assurance (from 2025) → Reasonable assurance (from 2028+)
- ESRS requires: Methodology disclosure, calculation standards (GHG Protocol), uncertainty disclosure
- Data quality factors:
  * Third-party verification: Independent auditor or IASP (Independent Assurance Service Provider)
  * Assurance level: Limited (review procedures) vs Reasonable (audit-level procedures)
  * Methodology: GHG Protocol, ISO 14064, sector-specific standards
  * Baseline quality: HIGH (verified, SBTi-validated) → MODERATE (self-reported) → LOW (no verification)

Assess this baseline data quality:

Baseline Value: {baseline_value}
Baseline Year: {baseline_year}
Third-Party Verified: {is_verified}
Verifier: {verifier if is_verified else 'None'}

Write 2-3 sentences assessing:
1. The quality and reliability of the baseline data
2. Whether verification level is adequate for SLL purposes
3. Any concerns about data methodology

Use professional banking language."""

        try:
            analysis = await self._call_ai(prompt)
            
            quality_score = "EXCELLENT" if is_verified else "MODERATE" if baseline_year else "WEAK"
            
            return {
                "detailed_analysis": analysis,
                "quality_score": quality_score,
                "verification_status": "Verified" if is_verified else "Unverified",
                "verifier": verifier if is_verified else None,
                "generated": True
            }
        except Exception as e:
            logger.error(f"Baseline analysis error: {e}")
            return {
                "detailed_analysis": f"Baseline of {baseline_value} from {baseline_year}. {'Externally verified.' if is_verified else 'No third-party verification disclosed.'}",
                "quality_score": "MODERATE",
                "verification_status": "Verified" if is_verified else "Unverified",
                "generated": False
            }
    
    async def _call_ai(self, prompt: str) -> str:
        """Call AI API for narrative generation."""
        # Try Perplexity first
        if settings.PERPLEXITY_API_KEY:
            try:
                response = await self.http_client.post(
                    settings.PERPLEXITY_API_URL,
                    json={
                        "model": settings.PERPLEXITY_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a senior sustainability finance analyst at a major European bank."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500
                    },
                    headers={
                        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                logger.warning(f"Perplexity call failed: {e}")
        
        # Fallback to Gemini
        if settings.GEMINI_API_KEY:
            try:
                response = await self.http_client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500}
                    }
                )
                response.raise_for_status()
                result = response.json()
                return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            except Exception as e:
                logger.warning(f"Gemini call failed: {e}")
        
        raise Exception("No AI API available")
    
    def _fallback_executive_summary(
        self,
        ambition_result: Dict,
        credibility_result: Dict,
        recommendation: str
    ) -> str:
        """Generate a fallback summary without AI."""
        classification = ambition_result.get('classification', 'UNKNOWN')
        target = ambition_result.get('borrower_target', 0)
        median = ambition_result.get('peer_median', 0)
        credibility = credibility_result.get('credibility_level', 'UNKNOWN')
        
        return f"The company's {target}% reduction target is classified as {classification} compared to the peer median of {median}%. Credibility assessment indicates {credibility} confidence in target achievability based on governance and verification signals. Overall recommendation: {recommendation}."
    
    def _fallback_ambition_analysis(self, ambition_result: Dict) -> str:
        """Fallback ambition analysis."""
        classification = ambition_result.get('classification', 'UNKNOWN')
        target = ambition_result.get('borrower_target', 0)
        median = ambition_result.get('peer_median', 0)
        
        analyses = {
            "WEAK": f"The target of {target}% falls below the peer median of {median}%, indicating below-market ambition. Consider negotiating target enhancement.",
            "MARKET_STANDARD": f"The target of {target}% aligns with market standard, positioned between peer median ({median}%) and 75th percentile.",
            "ABOVE_MARKET": f"The target of {target}% exceeds the 75th percentile, demonstrating above-market ambition.",
            "SCIENCE_ALIGNED": f"The target of {target}% is science-aligned, exceeding the 75th percentile with SBTi validation."
        }
        return analyses.get(classification, f"Target: {target}%, Classification: {classification}")
    
    def _fallback_credibility_analysis(self, credibility_result: Dict) -> str:
        """Fallback credibility analysis."""
        level = credibility_result.get('credibility_level', 'UNKNOWN')
        
        analyses = {
            "HIGH": "Strong credibility signals detected including past target achievement, third-party verification, and robust governance structures.",
            "MEDIUM": "Moderate credibility with some governance and verification signals present. Additional disclosure would strengthen the assessment.",
            "LOW": "Limited credibility indicators found. Recommend requesting additional documentation on governance and past performance."
        }
        return analyses.get(level, "Credibility assessment pending additional information.")
    
    def _extract_key_points(self, ambition: Dict, credibility: Dict, recommendation: str) -> list:
        """Extract key points for executive summary."""
        points = []
        
        classification = ambition.get('classification', '')
        if classification == 'SCIENCE_ALIGNED':
            points.append("Target is science-aligned with SBTi validation")
        elif classification == 'ABOVE_MARKET':
            points.append("Target exceeds 75th percentile peer benchmark")
        elif classification == 'MARKET_STANDARD':
            points.append("Target is in line with market standards")
        elif classification == 'WEAK':
            points.append("Target is below peer median - enhancement recommended")
        
        cred_level = credibility.get('credibility_level', '')
        if cred_level == 'HIGH':
            points.append("High credibility based on governance and verification")
        elif cred_level == 'MEDIUM':
            points.append("Moderate credibility - some signals present")
        elif cred_level == 'LOW':
            points.append("Low credibility - additional documentation needed")
        
        points.append(f"Recommendation: {recommendation}")
        
        return points
    
    def _get_classification_explanation(self, classification: str) -> str:
        """Get standard explanation for classification."""
        explanations = {
            "WEAK": "Below peer median indicates the target may not be sufficiently ambitious for sustainability-linked financing.",
            "MARKET_STANDARD": "Between median and 75th percentile represents acceptable ambition aligned with market practice.",
            "ABOVE_MARKET": "At or above 75th percentile demonstrates leadership-level ambition in emissions reduction.",
            "SCIENCE_ALIGNED": "Exceeds 75th percentile with SBTi validation, meeting the highest standard for climate-aligned targets."
        }
        return explanations.get(classification, "Classification pending peer data availability.")
    
    def _format_signals(self, signals: Dict) -> str:
        """Format signals for prompt."""
        lines = []
        for name, data in signals.items():
            if isinstance(data, dict):
                detected = "✓" if data.get('detected') else "✗"
                evidence = data.get('evidence', 'No evidence')
                lines.append(f"- {name}: {detected} ({evidence[:50]}...)" if len(str(evidence)) > 50 else f"- {name}: {detected} ({evidence})")
        return "\n".join(lines) if lines else "No signals data available"
    
    def _identify_strengths(self, signals: Dict) -> list:
        """Identify strength areas from signals."""
        strengths = []
        for name, data in signals.items():
            if isinstance(data, dict) and data.get('detected'):
                strengths.append(name.replace('_', ' ').title())
        return strengths
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()


# Singleton instance
ai_summary_service = AISummaryService()

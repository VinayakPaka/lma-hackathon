"""
GreenGuard ESG Platform - Credibility Assessment Service
Assesses target achievability using credibility signals (not complex math).
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.services.kpi_extraction_service import kpi_extraction_service
from app.services.sbti_data_service import sbti_data_service

logger = logging.getLogger(__name__)


@dataclass
class CredibilitySignal:
    """Represents a single credibility signal."""
    name: str
    detected: bool
    evidence: Optional[str] = None
    page_reference: Optional[int] = None
    weight: str = "medium"  # high, medium, low


class CredibilityAssessmentService:
    """
    Assess target achievability using credibility signals.
    
    Instead of complex mathematical forecasting, we assess achievability
    through observable credibility indicators:
    
    1. Past Targets Met - Historical track record
    2. Third-Party Verified - External validation
    3. Board Oversight - Governance strength
    4. Management Incentives - Alignment of interests
    5. SBTi Commitment - Science-based commitment
    6. Transition Plan - Concrete roadmap
    
    Classification:
    - HIGH: 4+ signals OR (past_targets + verified + board)
    - MEDIUM: 2-3 signals
    - LOW: 0-1 signals
    """
    
    SIGNAL_WEIGHTS = {
        "past_targets_met": "high",
        "third_party_verified": "high",
        "board_oversight": "medium",
        "management_incentives": "medium",
        "sbti_commitment": "high",
        "transition_plan": "medium"
    }
    
    async def assess_credibility(
        self,
        document_id: int,
        company_name: Optional[str] = None,
        extraction_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Perform full credibility assessment.
        
        Args:
            document_id: The document to analyze
            company_name: Optional company name for SBTi lookup
            extraction_data: Optional pre-extracted data (avoids duplicate extraction)
        
        Returns:
            Comprehensive credibility assessment
        """
        signals: Dict[str, CredibilitySignal] = {}
        
        try:
            # Use provided extraction or perform new extraction
            if extraction_data:
                extraction = extraction_data
            else:
                result = await kpi_extraction_service.extract_kpis_from_document(document_id)
                extraction = result.get("extraction", {}) if result.get("success") else {}
            
            # Signal 1: Past Targets Met
            past_perf = await kpi_extraction_service.search_for_past_targets(document_id)
            if past_perf.get("found"):
                perf_data = past_perf.get("past_performance", {})
                track_record = perf_data.get("overall_track_record", "unknown")
                signals["past_targets_met"] = CredibilitySignal(
                    name="Past Targets Met",
                    detected=track_record == "positive",
                    evidence="; ".join(perf_data.get("evidence_quotes", [])[:2]),
                    weight="high"
                )
            else:
                signals["past_targets_met"] = CredibilitySignal(
                    name="Past Targets Met",
                    detected=False,
                    weight="high"
                )
            
            # Signal 2: Third-Party Verified
            verification = extraction.get("verification", {})
            signals["third_party_verified"] = CredibilitySignal(
                name="Third-Party Verified",
                detected=bool(verification.get("third_party_verified")),
                evidence=verification.get("verifier_name"),
                page_reference=verification.get("page_reference"),
                weight="high"
            )
            
            # Signal 3: Board Oversight
            governance = extraction.get("governance", {})
            signals["board_oversight"] = CredibilitySignal(
                name="Board Oversight",
                detected=bool(governance.get("board_oversight")),
                evidence=governance.get("evidence_quote"),
                page_reference=governance.get("page_reference"),
                weight="medium"
            )
            
            # Signal 4: Management Incentives
            signals["management_incentives"] = CredibilitySignal(
                name="Management Incentives Linked",
                detected=bool(governance.get("management_incentives_linked")),
                evidence=governance.get("evidence_quote"),
                page_reference=governance.get("page_reference"),
                weight="medium"
            )
            
            # Signal 5: SBTi Commitment
            sbti_status = extraction.get("sbti_status", {})
            sbti_detected = bool(sbti_status.get("committed") or sbti_status.get("validated"))
            
            # Cross-reference with SBTi database if company name provided
            if company_name and not sbti_detected:
                sbti_check = sbti_data_service.check_sbti_commitment(company_name)
                sbti_detected = sbti_check.get("found", False)
                if sbti_detected:
                    sbti_status = {
                        "committed": True,
                        "status": sbti_check.get("status"),
                        "evidence_quote": f"Found in SBTi database: {sbti_check.get('company_name')}"
                    }
            
            signals["sbti_commitment"] = CredibilitySignal(
                name="SBTi Commitment",
                detected=sbti_detected,
                evidence=sbti_status.get("evidence_quote"),
                page_reference=sbti_status.get("page_reference"),
                weight="high"
            )
            
            # Signal 6: Transition Plan
            transition = extraction.get("transition_plan", {})
            signals["transition_plan"] = CredibilitySignal(
                name="Transition Plan",
                detected=bool(transition.get("has_plan")),
                evidence=transition.get("evidence_quote"),
                page_reference=transition.get("page_reference"),
                weight="medium"
            )
            
            # Classify overall credibility
            classification = self._classify_credibility(signals)
            
            return {
                "success": True,
                "document_id": document_id,
                "credibility_level": classification["level"],
                "credibility_rationale": classification["rationale"],
                "signals": {
                    name: {
                        "detected": signal.detected,
                        "evidence": signal.evidence,
                        "page_reference": signal.page_reference,
                        "weight": signal.weight
                    }
                    for name, signal in signals.items()
                },
                "signal_summary": {
                    "detected_count": classification["detected_count"],
                    "high_weight_detected": classification["high_weight_detected"],
                    "total_possible": len(signals),
                    "missing_signals": [
                        name for name, signal in signals.items() if not signal.detected
                    ]
                },
                "gaps": self._identify_gaps(signals),
                "assessment_method": "Credibility signal analysis (deterministic)"
            }
            
        except Exception as e:
            logger.error(f"Credibility assessment error: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id,
                "credibility_level": "UNKNOWN"
            }
    
    def _classify_credibility(self, signals: Dict[str, CredibilitySignal]) -> Dict[str, Any]:
        """
        Classify overall credibility level.
        
        Rules:
        - HIGH: 4+ signals OR (past_targets + verified + board)
        - MEDIUM: 2-3 signals
        - LOW: 0-1 signals
        """
        detected_signals = [name for name, signal in signals.items() if signal.detected]
        detected_count = len(detected_signals)
        
        # Check for high-confidence combination
        high_confidence_combo = all([
            signals.get("past_targets_met", CredibilitySignal("", False)).detected,
            signals.get("third_party_verified", CredibilitySignal("", False)).detected,
            signals.get("board_oversight", CredibilitySignal("", False)).detected
        ])
        
        # Count high-weight signals detected
        high_weight_detected = sum(
            1 for name, signal in signals.items()
            if signal.detected and signal.weight == "high"
        )
        
        if high_confidence_combo or detected_count >= 4:
            level = "HIGH"
            rationale = "Strong credibility based on multiple positive indicators"
        elif detected_count >= 2:
            level = "MEDIUM"
            rationale = f"Moderate credibility with {detected_count} signals present"
        else:
            level = "LOW"
            rationale = "Limited credibility indicators found"
        
        return {
            "level": level,
            "rationale": rationale,
            "detected_count": detected_count,
            "high_weight_detected": high_weight_detected,
            "high_confidence_combination": high_confidence_combo
        }
    
    def _identify_gaps(self, signals: Dict[str, CredibilitySignal]) -> List[Dict[str, str]]:
        """Identify gaps and recommendations."""
        gaps = []
        
        if not signals.get("past_targets_met", CredibilitySignal("", False)).detected:
            gaps.append({
                "signal": "Past Targets Met",
                "recommendation": "Request historical target performance data"
            })
        
        if not signals.get("third_party_verified", CredibilitySignal("", False)).detected:
            gaps.append({
                "signal": "Third-Party Verification",
                "recommendation": "Request independent verification of emissions data"
            })
        
        if not signals.get("board_oversight", CredibilitySignal("", False)).detected:
            gaps.append({
                "signal": "Board Oversight",
                "recommendation": "Request information on sustainability governance structure"
            })
        
        if not signals.get("management_incentives", CredibilitySignal("", False)).detected:
            gaps.append({
                "signal": "Management Incentives",
                "recommendation": "Inquire about sustainability-linked executive compensation"
            })
        
        if not signals.get("sbti_commitment", CredibilitySignal("", False)).detected:
            gaps.append({
                "signal": "SBTi Commitment",
                "recommendation": "Consider requiring SBTi commitment as loan condition"
            })
        
        if not signals.get("transition_plan", CredibilitySignal("", False)).detected:
            gaps.append({
                "signal": "Transition Plan",
                "recommendation": "Request detailed decarbonization roadmap with CAPEX plan"
            })
        
        return gaps
    
    async def quick_credibility_check(
        self,
        extraction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quick credibility check from pre-extracted data only.
        Does not re-query documents.
        """
        signals_detected = 0
        signals = []
        
        # Check verification
        if extraction.get("verification", {}).get("third_party_verified"):
            signals_detected += 1
            signals.append("third_party_verified")
        
        # Check governance
        gov = extraction.get("governance", {})
        if gov.get("board_oversight"):
            signals_detected += 1
            signals.append("board_oversight")
        if gov.get("management_incentives_linked"):
            signals_detected += 1
            signals.append("management_incentives")
        
        # Check SBTi
        if extraction.get("sbti_status", {}).get("committed"):
            signals_detected += 1
            signals.append("sbti_commitment")
        
        # Check transition plan
        if extraction.get("transition_plan", {}).get("has_plan"):
            signals_detected += 1
            signals.append("transition_plan")
        
        # Classify
        if signals_detected >= 4:
            level = "HIGH"
        elif signals_detected >= 2:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        return {
            "credibility_level": level,
            "signals_detected": signals_detected,
            "signals": signals
        }


# Singleton instance
credibility_service = CredibilityAssessmentService()

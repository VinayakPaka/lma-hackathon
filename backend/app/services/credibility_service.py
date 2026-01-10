"""
GreenGuard ESG Platform - Credibility Assessment Service
Assesses target achievability using credibility signals with point-based scoring.
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.services.kpi_extraction_service import kpi_extraction_service
from app.services.sbti_data_service import sbti_data_service
from app.services.sector_matching_service import sector_matching_service

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
    - HIGH: 4+ signals OR (past_targets + verified + board) OR score >= 70
    - MEDIUM-HIGH: score 50-69
    - MEDIUM: score 30-49 OR 2-3 signals
    - LOW: score < 30 OR 0-1 signals
    """
    
    # Point-based scoring system (total: 100 points)
    SIGNAL_POINTS = {
        "sbti_validation": 30,          # SBTi validated targets (strongest signal)
        "interim_target_exceeded": 25,   # Exceeding interim targets
        "multi_year_trajectory": 20,     # Consistent multi-year progress
        "third_party_verified": 15,      # Third-party verification
        "past_targets_met": 10,          # Historical target achievement
        "board_oversight": 10,           # Board-level governance
        "management_incentives": 10,     # ESG-linked compensation
        "transition_plan": 10,           # Concrete decarbonization roadmap
    }
    
    SIGNAL_WEIGHTS = {
        "past_targets_met": "high",
        "third_party_verified": "high",
        "board_oversight": "medium",
        "management_incentives": "medium",
        "sbti_commitment": "high",
        "transition_plan": "medium",
        "sbti_validation": "high",
        "interim_target_exceeded": "high",
        "multi_year_trajectory": "high"
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
        credibility_points = 0
        
        try:
            # Use provided extraction or perform new extraction
            if extraction_data:
                extraction = extraction_data
            else:
                result = await kpi_extraction_service.extract_kpis_from_document(document_id)
                extraction = result.get("extraction", {}) if result.get("success") else {}
            
            # ========================================
            # PRIORITY 1: SBTi Auto-Detection (NEW!)
            # If company is in SBTi database with validated targets,
            # this is the STRONGEST credibility signal
            # ========================================
            sbti_target_history = None
            if company_name:
                sbti_target_history = sector_matching_service.get_company_target_history(company_name)
                
                if sbti_target_history.get("found") and sbti_target_history.get("is_sbti_validated"):
                    # SBTi Validation signal (+30 points)
                    signals["sbti_validation"] = CredibilitySignal(
                        name="SBTi Validated Targets",
                        detected=True,
                        evidence=f"Company has {sbti_target_history.get('target_count', 0)} SBTi-validated targets",
                        weight="high"
                    )
                    credibility_points += self.SIGNAL_POINTS["sbti_validation"]
                    logger.info(f"SBTi validation detected for {company_name} (+30 points)")
                    
                    # Multi-year trajectory signal (+20 points)
                    trajectory = sbti_target_history.get("trajectory_info")
                    if trajectory:
                        signals["multi_year_trajectory"] = CredibilitySignal(
                            name="Multi-Year Trajectory",
                            detected=True,
                            evidence=f"Target trajectory: {trajectory.get('total_reduction_pct')}% reduction over {trajectory.get('years_to_target')} years ({trajectory.get('annual_reduction_rate')}%/year)",
                            weight="high"
                        )
                        credibility_points += self.SIGNAL_POINTS["multi_year_trajectory"]
                        logger.info(f"Multi-year trajectory detected for {company_name} (+20 points)")
            
            # Signal 1: Past Targets Met (+10 points)
            past_perf = await kpi_extraction_service.search_for_past_targets(document_id)
            if past_perf.get("found"):
                perf_data = past_perf.get("past_performance", {})
                track_record = perf_data.get("overall_track_record", "unknown")
                past_detected = track_record == "positive"
                signals["past_targets_met"] = CredibilitySignal(
                    name="Past Targets Met",
                    detected=past_detected,
                    evidence="; ".join(perf_data.get("evidence_quotes", [])[:2]),
                    weight="high"
                )
                if past_detected:
                    credibility_points += self.SIGNAL_POINTS["past_targets_met"]
            else:
                signals["past_targets_met"] = CredibilitySignal(
                    name="Past Targets Met",
                    detected=False,
                    weight="high"
                )
            
            # Signal 2: Third-Party Verified (+15 points)
            verification = extraction.get("verification", {})
            verified = bool(verification.get("third_party_verified"))
            signals["third_party_verified"] = CredibilitySignal(
                name="Third-Party Verified",
                detected=verified,
                evidence=verification.get("verifier_name"),
                page_reference=verification.get("page_reference"),
                weight="high"
            )
            if verified:
                credibility_points += self.SIGNAL_POINTS["third_party_verified"]
            
            # Signal 3: Board Oversight (+10 points)
            governance = extraction.get("governance", {})
            board_detected = bool(governance.get("board_oversight"))
            signals["board_oversight"] = CredibilitySignal(
                name="Board Oversight",
                detected=board_detected,
                evidence=governance.get("evidence_quote"),
                page_reference=governance.get("page_reference"),
                weight="medium"
            )
            if board_detected:
                credibility_points += self.SIGNAL_POINTS["board_oversight"]
            
            # Signal 4: Management Incentives (+10 points)
            mgmt_detected = bool(governance.get("management_incentives_linked"))
            signals["management_incentives"] = CredibilitySignal(
                name="Management Incentives Linked",
                detected=mgmt_detected,
                evidence=governance.get("evidence_quote"),
                page_reference=governance.get("page_reference"),
                weight="medium"
            )
            if mgmt_detected:
                credibility_points += self.SIGNAL_POINTS["management_incentives"]
            
            # Signal 5: SBTi Commitment (fallback if not already detected via validation)
            if "sbti_validation" not in signals:
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
                # Note: sbti_commitment gives fewer points than sbti_validation
                if sbti_detected:
                    credibility_points += 15  # Commitment without validation
            
            # Signal 6: Transition Plan (+10 points)
            transition = extraction.get("transition_plan", {})
            transition_detected = bool(transition.get("has_plan"))
            signals["transition_plan"] = CredibilitySignal(
                name="Transition Plan",
                detected=transition_detected,
                evidence=transition.get("evidence_quote"),
                page_reference=transition.get("page_reference"),
                weight="medium"
            )
            if transition_detected:
                credibility_points += self.SIGNAL_POINTS["transition_plan"]
            
            # Classify overall credibility using point-based system
            classification = self._classify_credibility(signals, credibility_points)
            
            # Include SBTi target history in return for PDF
            sbti_history_summary = None
            if sbti_target_history and sbti_target_history.get("found"):
                sbti_history_summary = {
                    "validated": sbti_target_history.get("is_sbti_validated"),
                    "target_count": sbti_target_history.get("target_count"),
                    "trajectory": sbti_target_history.get("trajectory_info"),
                    "near_term_targets": sbti_target_history.get("near_term_targets", [])[:2],
                    "long_term_targets": sbti_target_history.get("long_term_targets", [])[:2]
                }
            
            return {
                "success": True,
                "document_id": document_id,
                "credibility_level": classification["level"],
                "credibility_rationale": classification["rationale"],
                "credibility_score": credibility_points,  # NEW: Point-based score
                "max_possible_score": 100,
                "signals": {
                    name: {
                        "detected": signal.detected,
                        "evidence": signal.evidence,
                        "page_reference": signal.page_reference,
                        "weight": signal.weight,
                        "points": self.SIGNAL_POINTS.get(name, 0) if signal.detected else 0
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
                "sbti_history": sbti_history_summary,  # NEW: SBTi target history
                "gaps": self._identify_gaps(signals),
                "assessment_method": "Point-based credibility scoring (0-100)"
            }
            
        except Exception as e:
            logger.error(f"Credibility assessment error: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id,
                "credibility_level": "UNKNOWN"
            }
    
    def _classify_credibility(
        self,
        signals: Dict[str, CredibilitySignal],
        credibility_points: int = 0
    ) -> Dict[str, Any]:
        """
        Classify overall credibility level using point-based system.
        
        Classification:
        - HIGH: score >= 70 OR 4+ signals
        - MEDIUM-HIGH: score 50-69
        - MEDIUM: score 30-49 OR 2-3 signals
        - LOW: score < 30 OR 0-1 signals
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
        
        # Classify using BOTH point-based and signal-count methods
        # Point-based takes precedence when score is significant
        if credibility_points >= 70 or high_confidence_combo or detected_count >= 4:
            level = "HIGH"
            rationale = f"Strong credibility ({credibility_points}/100 points, {detected_count} signals detected)"
        elif credibility_points >= 50 or detected_count >= 3:
            level = "MEDIUM-HIGH"
            rationale = f"Good credibility ({credibility_points}/100 points, {detected_count} signals detected)"
        elif credibility_points >= 30 or detected_count >= 2:
            level = "MEDIUM"
            rationale = f"Moderate credibility ({credibility_points}/100 points, {detected_count} signals present)"
        else:
            level = "LOW"
            rationale = f"Limited credibility indicators ({credibility_points}/100 points, {detected_count} signals found)"
        
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

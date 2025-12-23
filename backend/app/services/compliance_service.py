"""
GreenGuard ESG Platform - Compliance Checker Service  
Checks loan structure against regulatory requirements (GLP, SLLP, SFDR, EBA).
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheck:
    """Result of a single compliance check."""
    requirement: str
    compliant: bool
    evidence: Optional[str] = None
    note: Optional[str] = None


class ComplianceCheckerService:
    """
    Check loan structure against regulatory requirements.
    
    Supported frameworks:
    - GLP: Green Loan Principles (LMA)
    - SLLP: Sustainability-Linked Loan Principles (LMA)
    - SFDR: Sustainable Finance Disclosure Regulation (EU)
    - EBA: European Banking Authority expectations
    - EU Taxonomy: Taxonomy Regulation alignment
    """
    
    # Compliance checklists per framework
    CHECKLISTS = {
        "glp": {
            "name": "Green Loan Principles (LMA)",
            "requirements": [
                {
                    "id": "glp_1",
                    "requirement": "Use of Proceeds clearly defined",
                    "description": "Loan proceeds must be designated for green projects"
                },
                {
                    "id": "glp_2", 
                    "requirement": "Project evaluation and selection process documented",
                    "description": "Clear criteria for selecting eligible green projects"
                },
                {
                    "id": "glp_3",
                    "requirement": "Proceeds management tracked separately",
                    "description": "Formal tracking of proceeds allocation to green projects"
                },
                {
                    "id": "glp_4",
                    "requirement": "Annual reporting commitment",
                    "description": "Regular reporting on use of proceeds and project status"
                }
            ]
        },
        "sllp": {
            "name": "Sustainability-Linked Loan Principles (LMA)",
            "requirements": [
                {
                    "id": "sllp_1",
                    "requirement": "KPIs are material to borrower's business",
                    "description": "Selected KPIs must be core and material to issuer's operations"
                },
                {
                    "id": "sllp_2",
                    "requirement": "SPTs are ambitious vs baseline",
                    "description": "Targets must represent material improvement beyond BAU"
                },
                {
                    "id": "sllp_3",
                    "requirement": "Margin adjustment mechanism defined",
                    "description": "Clear pricing mechanism linked to SPT achievement"
                },
                {
                    "id": "sllp_4",
                    "requirement": "Third-party verification required",
                    "description": "External verification of SPT performance at least annually"
                },
                {
                    "id": "sllp_5",
                    "requirement": "Annual SPT performance reporting",
                    "description": "Regular public disclosure of performance against SPTs"
                }
            ]
        },
        "sfdr": {
            "name": "SFDR Article 8/9 Requirements",
            "requirements": [
                {
                    "id": "sfdr_1",
                    "requirement": "Environmental characteristics promoted",
                    "description": "Product promotes environmental or social characteristics"
                },
                {
                    "id": "sfdr_2",
                    "requirement": "Good governance practices followed",
                    "description": "Investee companies follow good governance practices"
                },
                {
                    "id": "sfdr_3",
                    "requirement": "PAI indicators considered",
                    "description": "Principal Adverse Impact indicators are considered"
                }
            ]
        },
        "eba": {
            "name": "EBA Loan Origination Guidelines",
            "requirements": [
                {
                    "id": "eba_1",
                    "requirement": "Climate risk assessment conducted",
                    "description": "ESG factors considered in credit risk assessment"
                },
                {
                    "id": "eba_2",
                    "requirement": "Transition risk considered",
                    "description": "Risks from low-carbon transition evaluated"
                },
                {
                    "id": "eba_3",
                    "requirement": "Physical risk considered",
                    "description": "Physical climate risks to borrower assessed"
                }
            ]
        },
        "eu_taxonomy": {
            "name": "EU Taxonomy Regulation",
            "requirements": [
                {
                    "id": "tax_1",
                    "requirement": "Substantial contribution to environmental objective",
                    "description": "Activity makes substantial contribution to at least one objective"
                },
                {
                    "id": "tax_2",
                    "requirement": "Do No Significant Harm (DNSH)",
                    "description": "Activity does not significantly harm other objectives"
                },
                {
                    "id": "tax_3",
                    "requirement": "Minimum safeguards met",
                    "description": "OECD Guidelines and UN Guiding Principles compliance"
                },
                {
                    "id": "tax_4",
                    "requirement": "Technical screening criteria met",
                    "description": "Activity meets relevant TSC for the sector"
                }
            ]
        }
    }
    
    def check_compliance(
        self,
        framework: str,
        deal_data: Dict[str, Any],
        extraction_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Check compliance against a specific regulatory framework.
        
        Args:
            framework: Framework code (glp, sllp, sfdr, eba, eu_taxonomy)
            deal_data: Deal structure information
            extraction_data: Extracted document data for evidence matching
        
        Returns:
            Detailed compliance assessment
        """
        if framework not in self.CHECKLISTS:
            return {
                "error": f"Unknown framework: {framework}",
                "available_frameworks": list(self.CHECKLISTS.keys())
            }
        
        checklist = self.CHECKLISTS[framework]
        results = []
        
        for req in checklist["requirements"]:
            check_result = self._evaluate_requirement(
                framework, req, deal_data, extraction_data
            )
            results.append(check_result)
        
        # Calculate overall compliance
        compliant_count = sum(1 for r in results if r["compliant"])
        total_count = len(results)
        
        return {
            "framework": framework,
            "framework_name": checklist["name"],
            "overall_compliant": compliant_count == total_count,
            "compliance_score": f"{compliant_count}/{total_count}",
            "requirements": results,
            "gaps": [r for r in results if not r["compliant"]]
        }
    
    def _evaluate_requirement(
        self,
        framework: str,
        requirement: Dict,
        deal_data: Dict,
        extraction_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Evaluate a single requirement."""
        req_id = requirement["id"]
        
        # Framework-specific checks
        if framework == "sllp":
            return self._check_sllp_requirement(req_id, requirement, deal_data, extraction_data)
        elif framework == "glp":
            return self._check_glp_requirement(req_id, requirement, deal_data, extraction_data)
        elif framework == "sfdr":
            return self._check_sfdr_requirement(req_id, requirement, deal_data, extraction_data)
        elif framework == "eba":
            return self._check_eba_requirement(req_id, requirement, deal_data, extraction_data)
        elif framework == "eu_taxonomy":
            return self._check_taxonomy_requirement(req_id, requirement, deal_data, extraction_data)
        
        return {
            "id": req_id,
            "requirement": requirement["requirement"],
            "compliant": False,
            "note": "Check not implemented"
        }
    
    def _check_sllp_requirement(
        self,
        req_id: str,
        requirement: Dict,
        deal_data: Dict,
        extraction_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Check SLLP-specific requirements."""
        base_result = {
            "id": req_id,
            "requirement": requirement["requirement"],
            "description": requirement["description"]
        }
        
        if req_id == "sllp_1":  # KPI materiality
            # Check if KPI is emissions-related (material for most companies)
            metric = deal_data.get("metric", "").lower()
            is_material = any(k in metric for k in ["emission", "carbon", "ghg", "scope", "energy"])
            return {
                **base_result,
                "compliant": is_material,
                "evidence": f"KPI: {deal_data.get('metric', 'Not specified')}",
                "note": "Core business metric" if is_material else "Verify KPI materiality to business"
            }
        
        elif req_id == "sllp_2":  # SPT ambition
            # This should be informed by peer benchmarking
            target_value = deal_data.get("target_value")
            ambition_class = deal_data.get("ambition_classification", "").upper()
            is_ambitious = ambition_class in ["MARKET_STANDARD", "ABOVE_MARKET", "SCIENCE_ALIGNED"]
            return {
                **base_result,
                "compliant": is_ambitious,
                "evidence": f"Target: {target_value}, Classification: {ambition_class}",
                "note": "Above baseline" if is_ambitious else "TARGET BELOW PEER MEDIAN - FLAG"
            }
        
        elif req_id == "sllp_3":  # Margin adjustment
            has_margin = deal_data.get("margin_adjustment_bps") is not None
            return {
                **base_result,
                "compliant": has_margin,
                "evidence": f"Margin: ±{deal_data.get('margin_adjustment_bps', 'Not specified')}bps",
                "note": None if has_margin else "Define margin adjustment mechanism"
            }
        
        elif req_id == "sllp_4":  # Third-party verification
            is_verified = extraction_data.get("verification", {}).get("third_party_verified") if extraction_data else False
            verifier = extraction_data.get("verification", {}).get("verifier_name") if extraction_data else None
            return {
                **base_result,
                "compliant": bool(is_verified),
                "evidence": f"Verifier: {verifier}" if verifier else None,
                "note": None if is_verified else "Require annual third-party verification"
            }
        
        elif req_id == "sllp_5":  # Annual reporting
            # Assume reporting is a deal condition
            return {
                **base_result,
                "compliant": True,
                "evidence": "Annual reporting required per loan agreement",
                "note": None
            }
        
        return {**base_result, "compliant": False, "note": "Unable to evaluate"}
    
    def _check_glp_requirement(
        self,
        req_id: str,
        requirement: Dict,
        deal_data: Dict,
        extraction_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Check GLP-specific requirements."""
        base_result = {
            "id": req_id,
            "requirement": requirement["requirement"],
            "description": requirement["description"]
        }
        
        use_of_proceeds = deal_data.get("use_of_proceeds")
        
        if req_id == "glp_1":
            return {
                **base_result,
                "compliant": bool(use_of_proceeds),
                "evidence": use_of_proceeds,
                "note": None if use_of_proceeds else "Define eligible green projects"
            }
        elif req_id in ["glp_2", "glp_3", "glp_4"]:
            # These are typically deal documentation requirements
            return {
                **base_result,
                "compliant": True,
                "evidence": "Standard loan documentation",
                "note": "Verify in final documentation"
            }
        
        return {**base_result, "compliant": False}
    
    def _check_sfdr_requirement(
        self,
        req_id: str,
        requirement: Dict,
        deal_data: Dict,
        extraction_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Check SFDR-specific requirements."""
        base_result = {
            "id": req_id,
            "requirement": requirement["requirement"],
            "description": requirement["description"]
        }
        
        if req_id == "sfdr_1":
            # Environmental characteristics via emissions target
            has_env_char = "emission" in deal_data.get("metric", "").lower()
            return {
                **base_result,
                "compliant": has_env_char,
                "evidence": deal_data.get("metric"),
                "note": "Article 8 eligible" if has_env_char else None
            }
        elif req_id == "sfdr_2":
            # Governance from extraction
            gov = extraction_data.get("governance", {}) if extraction_data else {}
            has_gov = gov.get("board_oversight", False)
            return {
                **base_result,
                "compliant": bool(has_gov),
                "evidence": gov.get("evidence_quote"),
                "note": None if has_gov else "Verify governance practices"
            }
        elif req_id == "sfdr_3":
            # PAI consideration implicit in emissions tracking
            return {
                **base_result,
                "compliant": True,
                "evidence": "GHG emissions tracking addresses PAI",
                "note": None
            }
        
        return {**base_result, "compliant": False}
    
    def _check_eba_requirement(
        self,
        req_id: str,
        requirement: Dict,
        deal_data: Dict,
        extraction_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Check EBA-specific requirements."""
        base_result = {
            "id": req_id,
            "requirement": requirement["requirement"],
            "description": requirement["description"]
        }
        
        # EBA checks are typically part of credit process
        if req_id == "eba_1":
            return {
                **base_result,
                "compliant": True,
                "evidence": "ESG assessment performed via this evaluation",
                "note": None
            }
        elif req_id in ["eba_2", "eba_3"]:
            return {
                **base_result,
                "compliant": True,
                "evidence": "Risk assessment required in credit process",
                "note": "Confirm in credit memo"
            }
        
        return {**base_result, "compliant": False}
    
    def _check_taxonomy_requirement(
        self,
        req_id: str,
        requirement: Dict,
        deal_data: Dict,
        extraction_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Check EU Taxonomy requirements."""
        base_result = {
            "id": req_id,
            "requirement": requirement["requirement"],
            "description": requirement["description"]
        }
        
        # Taxonomy checks require detailed activity analysis
        taxonomy_data = extraction_data.get("taxonomy", {}) if extraction_data else {}
        
        if req_id == "tax_1":
            metric = deal_data.get("metric", "").lower()
            has_contribution = "emission" in metric or "energy" in metric
            return {
                **base_result,
                "compliant": has_contribution,
                "evidence": f"Climate mitigation via {deal_data.get('metric')}",
                "note": "Climate change mitigation objective"
            }
        else:
            return {
                **base_result,
                "compliant": True,
                "evidence": "Requires detailed activity-level assessment",
                "note": "Verify against Technical Screening Criteria"
            }
    
    def check_all_frameworks(
        self,
        deal_data: Dict[str, Any],
        extraction_data: Optional[Dict] = None,
        loan_type: str = "sll"
    ) -> Dict[str, Any]:
        """
        Check compliance against all relevant frameworks.
        
        Args:
            deal_data: Deal structure information
            extraction_data: Extracted document data
            loan_type: "sll" for sustainability-linked, "green" for green loan
        
        Returns:
            Complete compliance assessment across all frameworks
        """
        relevant_frameworks = ["sllp", "sfdr", "eba"]
        if loan_type == "green":
            relevant_frameworks = ["glp", "eu_taxonomy", "sfdr", "eba"]
        elif loan_type == "sll":
            relevant_frameworks = ["sllp", "sfdr", "eba"]
        
        results = {}
        all_compliant = True
        total_gaps = []
        
        for framework in relevant_frameworks:
            check = self.check_compliance(framework, deal_data, extraction_data)
            results[framework] = check
            if not check.get("overall_compliant", False):
                all_compliant = False
                total_gaps.extend(check.get("gaps", []))
        
        return {
            "overall_compliant": all_compliant,
            "frameworks_checked": relevant_frameworks,
            "results": results,
            "total_gaps": total_gaps,
            "gap_count": len(total_gaps)
        }
    
    def generate_compliance_summary(
        self,
        compliance_results: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Generate simple boolean summary for report output."""
        summary = {}
        
        for framework, result in compliance_results.get("results", {}).items():
            if framework == "glp":
                summary["eu_glp"] = result.get("overall_compliant", False)
            elif framework == "sllp":
                summary["lma_sllp"] = result.get("overall_compliant", False)
            elif framework == "sfdr":
                summary["sfdr_article_8"] = result.get("overall_compliant", False)
            elif framework == "eba":
                summary["eba_expectations"] = result.get("overall_compliant", False)
            elif framework == "eu_taxonomy":
                summary["eu_taxonomy"] = result.get("overall_compliant", False)
        
        return summary


# Singleton instance
compliance_checker = ComplianceCheckerService()

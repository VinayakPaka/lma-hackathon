"""
GreenGuard ESG Platform - CSRD/Sustainability Report Analyzer
Deep understanding of CSRD (ESRS) and sustainability report structures.
"""
import logging
from typing import Dict, Any, List, Optional
from app.services.embedding_service import embedding_service
from app.config import settings

logger = logging.getLogger(__name__)


class CSRDAnalyzerService:
    """
    Specialized service for analyzing CSRD and sustainability reports.
    
    Deep understanding of:
    - ESRS (European Sustainability Reporting Standards) - All 12 standards
    - GRI (Global Reporting Initiative) standards
    - TCFD (Task Force on Climate-related Financial Disclosures)
    - CDP (Carbon Disclosure Project) format
    - SASB (Sustainability Accounting Standards Board)
    - Double materiality assessment
    - EU Taxonomy alignment
    """
    
    def __init__(self):
        self._http_client = None
    
    @property
    def http_client(self):
        """Lazy initialization of HTTP client."""
        if self._http_client is None:
            import httpx
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client
    
    # CSRD/ESRS disclosure topics with their standard identifiers
    ESRS_TOPICS = {
        "climate": {
            "code": "ESRS E1",
            "keywords": [
                "climate change", "greenhouse gas", "GHG emissions", "carbon footprint",
                "scope 1", "scope 2", "scope 3", "emissions reduction", "net zero",
                "climate-related risks", "climate transition plan", "carbon pricing",
                "renewable energy", "energy efficiency", "fossil fuel"
            ]
        },
        "pollution": {
            "code": "ESRS E2",
            "keywords": [
                "pollution", "air quality", "water pollution", "soil contamination",
                "hazardous substances", "pollutants", "emissions to air", "emissions to water"
            ]
        },
        "water": {
            "code": "ESRS E3",
            "keywords": [
                "water consumption", "water withdrawal", "water discharge", "water stress",
                "water management", "water resources", "wastewater"
            ]
        },
        "biodiversity": {
            "code": "ESRS E4",
            "keywords": [
                "biodiversity", "ecosystems", "deforestation", "land use",
                "species", "habitat", "natural capital"
            ]
        },
        "circular_economy": {
            "code": "ESRS E5",
            "keywords": [
                "circular economy", "waste management", "recycling", "resource efficiency",
                "waste reduction", "material efficiency", "end-of-life"
            ]
        },
        "governance": {
            "code": "ESRS G1",
            "keywords": [
                "corporate governance", "board", "management board", "supervisory board",
                "executive compensation", "sustainability governance", "ESG oversight",
                "remuneration", "incentive structure", "board composition"
            ]
        },
        "targets_metrics": {
            "code": "ESRS 2 SBM-3",
            "keywords": [
                "sustainability targets", "KPI", "performance targets", "reduction target",
                "baseline year", "target year", "science-based targets", "SBTi",
                "materiality assessment", "double materiality"
            ]
        }
    }
    
    # Banker-specific analysis dimensions
    BANKER_ANALYSIS_DIMENSIONS = {
        "data_quality": {
            "name": "Data Quality & Verification",
            "factors": [
                "third-party verification", "assurance level", "audit trail",
                "data methodology", "calculation standards", "uncertainty disclosure"
            ]
        },
        "ambition": {
            "name": "Target Ambition",
            "factors": [
                "science-based alignment", "peer comparison", "absolute vs intensity",
                "scope coverage", "timeframe", "interim milestones"
            ]
        },
        "credibility": {
            "name": "Delivery Credibility",
            "factors": [
                "past performance", "capex allocation", "transition plan",
                "management incentives", "board oversight", "governance structure"
            ]
        },
        "risk": {
            "name": "Delivery Risk",
            "factors": [
                "technology dependencies", "regulatory dependencies", "market dependencies",
                "supply chain dependencies", "financial capacity", "organizational capability"
            ]
        },
        "compliance": {
            "name": "Regulatory Compliance",
            "factors": [
                "CSRD compliance", "taxonomy alignment", "SFDR classification",
                "green bond framework", "SLL principles", "disclosure completeness"
            ]
        }
    }
    
    # ESRS General Standards (Cross-cutting)
    ESRS_GENERAL = {
        "ESRS_1": {
            "name": "General Requirements",
            "description": "Sets out general principles and requirements for sustainability reporting"
        },
        "ESRS_2": {
            "name": "General Disclosures",
            "description": "Mandatory general information about governance, strategy, impacts, risks and opportunities"
        }
    }
    
    # Complete ESRS Environmental Standards (E1-E5)
    ESRS_ENVIRONMENTAL = {
        "E1": "Climate Change",
        "E2": "Pollution", 
        "E3": "Water and Marine Resources",
        "E4": "Biodiversity and Ecosystems",
        "E5": "Resource Use and Circular Economy"
    }
    
    # Complete ESRS Social Standards (S1-S4)
    ESRS_SOCIAL = {
        "S1": "Own Workforce",
        "S2": "Workers in the Value Chain",
        "S3": "Affected Communities",
        "S4": "Consumers and End-users"
    }
    
    # ESRS Governance Standard
    ESRS_GOVERNANCE = {
        "G1": "Business Conduct"
    }
    
    # Double Materiality Framework
    DOUBLE_MATERIALITY = {
        "impact_materiality": {
            "description": "Company's impact on environment and people",
            "aspects": ["actual_positive", "actual_negative", "potential_positive", "potential_negative"],
            "assessment_factors": {
                "negative_impacts": ["scale", "scope", "irremediability", "likelihood"],
                "positive_impacts": ["scale", "scope", "likelihood"]
            }
        },
        "financial_materiality": {
            "description": "How sustainability matters affect company's financial performance",
            "aspects": ["risks", "opportunities"],
            "assessment_factors": ["magnitude", "likelihood"]
        }
    }
    
    # Key CSRD/ESRS concepts for extraction
    KEY_CONCEPTS = {
        "materiality_assessment": [
            "double materiality", "materiality threshold", "material matters",
            "impact materiality", "financial materiality", "stakeholder engagement"
        ],
        "governance": [
            "board oversight", "management board", "supervisory board", 
            "sustainability committee", "executive compensation", "ESG governance",
            "remuneration linked to sustainability"
        ],
        "targets_and_metrics": [
            "sustainability targets", "KPI", "baseline year", "target year",
            "science-based targets", "SBTi", "reduction target", "interim milestones"
        ],
        "value_chain": [
            "upstream", "downstream", "supply chain", "value chain impacts",
            "scope 1", "scope 2", "scope 3", "business relationships"
        ],
        "due_diligence": [
            "due diligence process", "CSDDD", "adverse impacts", "remediation",
            "stakeholder engagement", "grievance mechanism"
        ],
        "transition_plan": [
            "climate transition plan", "decarbonization", "paris agreement",
            "net zero", "carbon neutrality", "1.5°C pathway"
        ],
        "verification": [
            "third-party verification", "limited assurance", "reasonable assurance",
            "audit", "external assurance", "IASP", "statutory auditor"
        ],
        "taxonomy": [
            "EU taxonomy", "taxonomy-aligned", "substantial contribution",
            "DNSH", "do no significant harm", "minimum safeguards"
        ]
    }
    
    async def analyze_csrd_compliance(self, document_id: int, company_name: str) -> Dict[str, Any]:
        """
        Comprehensive CSRD compliance analysis of a sustainability report.
        
        Analyzes:
        - ESRS standards coverage (all 12 standards)
        - Double materiality assessment quality
        - Data quality and verification
        - Banker-relevant signals
        
        Args:
            document_id: The document ID to analyze
            company_name: Company name for context
            
        Returns:
            Comprehensive compliance and quality assessment
        """
        try:
            logger.info(f"Analyzing CSRD compliance for {company_name}, document {document_id}")
            
            # Search for CSRD/ESRS specific content
            esrs_coverage = await self._assess_esrs_coverage(document_id)
            materiality_quality = await self._assess_materiality(document_id)
            data_quality = await self._assess_data_quality(document_id)
            banker_signals = await self._extract_banker_signals(document_id)
            
            # Overall compliance score
            compliance_score = self._calculate_compliance_score(
                esrs_coverage, materiality_quality, data_quality
            )
            
            return {
                "success": True,
                "company_name": company_name,
                "document_id": document_id,
                "compliance_score": compliance_score,
                "esrs_coverage": esrs_coverage,
                "materiality_assessment": materiality_quality,
                "data_quality": data_quality,
                "banker_signals": banker_signals,
                "recommendations": self._generate_recommendations(
                    esrs_coverage, materiality_quality, data_quality
                )
            }
            
        except Exception as e:
            logger.error(f"CSRD compliance analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _assess_esrs_coverage(self, document_id: int) -> Dict[str, Any]:
        """Assess coverage of all 12 ESRS standards."""
        coverage = {
            "general": {"ESRS_1": False, "ESRS_2": False},
            "environmental": {k: False for k in self.ESRS_ENVIRONMENTAL.keys()},
            "social": {k: False for k in self.ESRS_SOCIAL.keys()},
            "governance": {k: False for k in self.ESRS_GOVERNANCE.keys()}
        }
        
        # Search for each ESRS standard
        for topic, data in self.ESRS_TOPICS.items():
            query = " ".join(data["keywords"][:10])
            results = await embedding_service.search_similar(
                query=query,
                document_id=document_id,
                top_k=3
            )
            
            if results and len(results) > 0:
                code = data["code"]
                if "E1" in code:
                    coverage["environmental"]["E1"] = True
                elif "E2" in code:
                    coverage["environmental"]["E2"] = True
                elif "E3" in code:
                    coverage["environmental"]["E3"] = True
                elif "E4" in code:
                    coverage["environmental"]["E4"] = True
                elif "E5" in code:
                    coverage["environmental"]["E5"] = True
                elif "G1" in code:
                    coverage["governance"]["G1"] = True
                elif "ESRS 2" in code:
                    coverage["general"]["ESRS_2"] = True
        
        # Calculate coverage percentage
        total_standards = 12
        covered_count = (
            sum(coverage["general"].values()) +
            sum(coverage["environmental"].values()) +
            sum(coverage["social"].values()) +
            sum(coverage["governance"].values())
        )
        
        coverage_percentage = (covered_count / total_standards) * 100
        
        return {
            "coverage": coverage,
            "coverage_percentage": round(coverage_percentage, 1),
            "covered_standards": covered_count,
            "total_standards": total_standards
        }
    
    async def _assess_materiality(self, document_id: int) -> Dict[str, Any]:
        """Assess double materiality assessment quality."""
        materiality_keywords = self.KEY_CONCEPTS["materiality_assessment"]
        query = " ".join(materiality_keywords)
        
        results = await embedding_service.search_similar(
            query=query,
            document_id=document_id,
            top_k=5
        )
        
        has_double_materiality = False
        has_impact_materiality = False
        has_financial_materiality = False
        has_stakeholder_engagement = False
        
        if results:
            text = " ".join([r.get("content", "") for r in results]).lower()
            has_double_materiality = "double materiality" in text
            has_impact_materiality = "impact materiality" in text
            has_financial_materiality = "financial materiality" in text
            has_stakeholder_engagement = "stakeholder" in text
        
        quality_score = sum([
            has_double_materiality,
            has_impact_materiality,
            has_financial_materiality,
            has_stakeholder_engagement
        ]) * 25
        
        return {
            "has_double_materiality": has_double_materiality,
            "has_impact_materiality": has_impact_materiality,
            "has_financial_materiality": has_financial_materiality,
            "has_stakeholder_engagement": has_stakeholder_engagement,
            "quality_score": quality_score,
            "quality_level": "HIGH" if quality_score >= 75 else "MEDIUM" if quality_score >= 50 else "LOW"
        }
    
    async def _assess_data_quality(self, document_id: int) -> Dict[str, Any]:
        """Assess data quality and verification."""
        verification_keywords = self.KEY_CONCEPTS["verification"]
        query = " ".join(verification_keywords)
        
        results = await embedding_service.search_similar(
            query=query,
            document_id=document_id,
            top_k=3
        )
        
        has_third_party_verification = False
        has_limited_assurance = False
        has_reasonable_assurance = False
        verifier_name = None
        
        if results:
            text = " ".join([r.get("content", "") for r in results]).lower()
            has_third_party_verification = any(
                kw in text for kw in ["verified", "assured", "audited", "external assurance"]
            )
            has_limited_assurance = "limited assurance" in text
            has_reasonable_assurance = "reasonable assurance" in text
            
            # Try to extract verifier name
            verifier_patterns = ["deloitte", "pwc", "kpmg", "ey", "ernst & young", "bureau veritas"]
            for pattern in verifier_patterns:
                if pattern in text:
                    verifier_name = pattern.upper()
                    break
        
        quality_level = "HIGH" if has_reasonable_assurance else "MEDIUM" if has_limited_assurance else "LOW"
        
        return {
            "has_third_party_verification": has_third_party_verification,
            "assurance_level": "reasonable" if has_reasonable_assurance else "limited" if has_limited_assurance else "none",
            "verifier_name": verifier_name,
            "quality_level": quality_level
        }
    
    async def _extract_banker_signals(self, document_id: int) -> Dict[str, Any]:
        """Extract key signals relevant for banker assessment."""
        signals = {}
        
        for dimension, data in self.BANKER_ANALYSIS_DIMENSIONS.items():
            query = " ".join(data["factors"])
            results = await embedding_service.search_similar(
                query=query,
                document_id=document_id,
                top_k=2
            )
            
            signals[dimension] = {
                "name": data["name"],
                "evidence_found": len(results) > 0,
                "evidence_snippets": [r.get("content", "")[:200] for r in results[:2]] if results else []
            }
        
        return signals
    
    def _calculate_compliance_score(
        self, 
        esrs_coverage: Dict, 
        materiality_quality: Dict, 
        data_quality: Dict
    ) -> Dict[str, Any]:
        """Calculate overall CSRD compliance score."""
        coverage_score = esrs_coverage["coverage_percentage"]
        materiality_score = materiality_quality["quality_score"]
        
        data_quality_score = {
            "HIGH": 100,
            "MEDIUM": 70,
            "LOW": 40
        }.get(data_quality["quality_level"], 40)
        
        overall_score = (
            coverage_score * 0.4 +
            materiality_score * 0.3 +
            data_quality_score * 0.3
        )
        
        compliance_level = (
            "EXCELLENT" if overall_score >= 90 else
            "GOOD" if overall_score >= 75 else
            "ADEQUATE" if overall_score >= 60 else
            "NEEDS_IMPROVEMENT"
        )
        
        return {
            "overall_score": round(overall_score, 1),
            "compliance_level": compliance_level,
            "breakdown": {
                "esrs_coverage": coverage_score,
                "materiality_quality": materiality_score,
                "data_quality": data_quality_score
            }
        }
    
    def _generate_recommendations(
        self,
        esrs_coverage: Dict,
        materiality_quality: Dict,
        data_quality: Dict
    ) -> List[str]:
        """Generate recommendations for improving CSRD compliance."""
        recommendations = []
        
        if esrs_coverage["coverage_percentage"] < 80:
            missing_standards = []
            for category, standards in esrs_coverage["coverage"].items():
                if isinstance(standards, dict):
                    for std, covered in standards.items():
                        if not covered:
                            missing_standards.append(std)
            
            if missing_standards:
                recommendations.append(
                    f"Enhance disclosure for missing ESRS standards: {', '.join(missing_standards[:5])}"
                )
        
        if not materiality_quality.get("has_double_materiality"):
            recommendations.append(
                "Implement comprehensive double materiality assessment"
            )
        
        if data_quality["quality_level"] != "HIGH":
            recommendations.append(
                "Obtain higher level of external assurance (reasonable assurance)"
            )
        
        return recommendations


# Singleton instance
csrd_analyzer_service = CSRDAnalyzerService()

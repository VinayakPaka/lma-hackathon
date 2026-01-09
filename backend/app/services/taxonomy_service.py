"""
GreenGuard ESG Platform - EU Taxonomy Service
Understands EU Taxonomy Regulation and alignment criteria.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class TaxonomyService:
    """
    Service for analyzing EU Taxonomy alignment in sustainability reports.
    
    Understands:
    - EU Taxonomy Regulation (2020/852)
    - Six environmental objectives
    - Technical screening criteria
    - DNSH (Do No Significant Harm) principle
    - Minimum social safeguards
    """
    
    # Six EU Taxonomy Environmental Objectives
    ENVIRONMENTAL_OBJECTIVES = {
        "climate_mitigation": {
            "code": "1",
            "name": "Climate change mitigation",
            "description": "Activities that substantially contribute to stabilizing greenhouse gas concentrations",
            "keywords": [
                "climate mitigation", "GHG reduction", "emissions reduction",
                "renewable energy", "energy efficiency", "low-carbon technology",
                "carbon capture", "sustainable transport", "green buildings"
            ]
        },
        "climate_adaptation": {
            "code": "2",
            "name": "Climate change adaptation",
            "description": "Activities that reduce risk of adverse effects of current/expected future climate",
            "keywords": [
                "climate adaptation", "climate resilience", "climate risk",
                "adaptation solutions", "nature-based solutions", "climate-resilient infrastructure"
            ]
        },
        "water": {
            "code": "3",
            "name": "Sustainable use and protection of water and marine resources",
            "description": "Activities that contribute to good status of water bodies and marine waters",
            "keywords": [
                "water conservation", "water efficiency", "water protection",
                "marine conservation", "wastewater treatment", "water stress"
            ]
        },
        "circular_economy": {
            "code": "4",
            "name": "Transition to a circular economy",
            "description": "Activities that contribute to circular economy including waste prevention and recycling",
            "keywords": [
                "circular economy", "waste prevention", "recycling", "reuse",
                "resource efficiency", "material recovery", "product lifetime extension"
            ]
        },
        "pollution": {
            "code": "5",
            "name": "Pollution prevention and control",
            "description": "Activities that contribute to environmental protection from pollution",
            "keywords": [
                "pollution prevention", "pollution control", "emissions reduction",
                "clean air", "clean water", "soil remediation", "hazardous substances"
            ]
        },
        "biodiversity": {
            "code": "6",
            "name": "Protection and restoration of biodiversity and ecosystems",
            "description": "Activities that contribute to protecting, conserving or restoring biodiversity",
            "keywords": [
                "biodiversity protection", "ecosystem restoration", "conservation",
                "deforestation-free", "sustainable land use", "nature conservation"
            ]
        }
    }
    
    # DNSH (Do No Significant Harm) Criteria
    DNSH_CRITERIA = {
        "description": "Activity must not significantly harm any of the other 5 environmental objectives",
        "examples": [
            "Renewable energy project must not harm biodiversity (no wind farms in protected areas)",
            "Energy efficiency retrofit must use sustainable materials (circular economy)",
            "Transport project must minimize pollution and protect water resources"
        ]
    }
    
    # Minimum Social Safeguards
    MINIMUM_SAFEGUARDS = {
        "description": "Alignment with OECD Guidelines and UN Guiding Principles on Business and Human Rights",
        "requirements": [
            "Human rights due diligence",
            "No child labor or forced labor",
            "Fair working conditions",
            "Anti-corruption measures",
            "Fair competition",
            "Tax compliance"
        ]
    }
    
    # Three KPIs required for CSRD reporting
    TAXONOMY_KPIS = {
        "turnover": {
            "name": "Proportion of turnover from Taxonomy-aligned activities",
            "description": "% of net turnover from products/services associated with taxonomy-aligned economic activities",
            "mandatory_for": ["all_companies"]
        },
        "capex": {
            "name": "Proportion of CapEx from Taxonomy-aligned activities",
            "description": "% of capital expenditure related to assets/processes associated with taxonomy-aligned activities",
            "mandatory_for": ["all_companies"]
        },
        "opex": {
            "name": "Proportion of OpEx from Taxonomy-aligned activities",
            "description": "% of operating expenditure related to assets/processes associated with taxonomy-aligned activities",
            "mandatory_for": ["all_companies"]
        }
    }
    
    async def analyze_taxonomy_alignment(
        self,
        document_id: int,
        company_name: str,
        embedding_service
    ) -> Dict[str, Any]:
        """
        Analyze EU Taxonomy alignment disclosed in sustainability report.
        
        Args:
            document_id: Document ID to analyze
            company_name: Company name
            embedding_service: Embedding service for RAG search
            
        Returns:
            Taxonomy alignment analysis
        """
        try:
            logger.info(f"Analyzing EU Taxonomy alignment for {company_name}")
            
            # Search for taxonomy-related content
            taxonomy_keywords = "EU Taxonomy taxonomy-aligned substantial contribution DNSH turnover CapEx OpEx environmental objectives"
            
            results = await embedding_service.search_similar(
                query=taxonomy_keywords,
                document_id=document_id,
                top_k=10
            )
            
            if not results or len(results) == 0:
                return {
                    "taxonomy_disclosed": False,
                    "message": "No EU Taxonomy disclosure found in document"
                }
            
            # Extract text for analysis
            text = " ".join([r.get("content", "") for r in results]).lower()
            
            # Check if taxonomy is mentioned
            taxonomy_mentioned = any(kw in text for kw in ["taxonomy", "taxonomy-aligned", "taxonomy alignment"])
            
            if not taxonomy_mentioned:
                return {
                    "taxonomy_disclosed": False,
                    "message": "EU Taxonomy not mentioned in document"
                }
            
            # Analyze KPI disclosure
            kpi_disclosure = self._analyze_kpi_disclosure(text, results)
            
            # Analyze environmental objectives
            objectives_analysis = self._analyze_objectives(text)
            
            # Check DNSH and safeguards
            dnsh_mentioned = "dnsh" in text or "do no significant harm" in text
            safeguards_mentioned = any(kw in text for kw in ["minimum safeguards", "social safeguards", "human rights"])
            
            # Calculate alignment quality score
            quality_score = self._calculate_taxonomy_quality(
                kpi_disclosure,
                objectives_analysis,
                dnsh_mentioned,
                safeguards_mentioned
            )
            
            return {
                "taxonomy_disclosed": True,
                "company_name": company_name,
                "kpi_disclosure": kpi_disclosure,
                "environmental_objectives": objectives_analysis,
                "dnsh_mentioned": dnsh_mentioned,
                "safeguards_mentioned": safeguards_mentioned,
                "quality_score": quality_score,
                "evidence_snippets": [r.get("content", "")[:300] for r in results[:3]]
            }
            
        except Exception as e:
            logger.error(f"Taxonomy analysis error: {e}")
            return {
                "taxonomy_disclosed": False,
                "error": str(e)
            }
    
    def _analyze_kpi_disclosure(self, text: str, results: List[Dict]) -> Dict[str, Any]:
        """Analyze disclosure of three mandatory KPIs."""
        kpis_found = {}
        
        for kpi_name, kpi_data in self.TAXONOMY_KPIS.items():
            # Check if KPI is mentioned
            mentioned = kpi_name in text or kpi_data["name"].lower() in text
            
            # Try to extract percentage if mentioned
            percentage = None
            if mentioned:
                # Simple pattern matching for percentages near the KPI name
                for result in results:
                    content = result.get("content", "").lower()
                    if kpi_name in content:
                        # Look for percentage patterns
                        import re
                        matches = re.findall(r'(\d+(?:\.\d+)?)\s*%', content)
                        if matches:
                            try:
                                percentage = float(matches[0])
                            except:
                                pass
                        break
            
            kpis_found[kpi_name] = {
                "disclosed": mentioned,
                "percentage": percentage,
                "description": kpi_data["description"]
            }
        
        all_disclosed = all(kpi["disclosed"] for kpi in kpis_found.values())
        
        return {
            "all_three_kpis_disclosed": all_disclosed,
            "kpis": kpis_found
        }
    
    def _analyze_objectives(self, text: str) -> Dict[str, Any]:
        """Analyze which environmental objectives are addressed."""
        objectives_found = {}
        
        for obj_key, obj_data in self.ENVIRONMENTAL_OBJECTIVES.items():
            # Check if objective is mentioned
            mentioned = any(keyword in text for keyword in obj_data["keywords"])
            
            objectives_found[obj_key] = {
                "code": obj_data["code"],
                "name": obj_data["name"],
                "mentioned": mentioned
            }
        
        objectives_count = sum(1 for obj in objectives_found.values() if obj["mentioned"])
        
        return {
            "objectives": objectives_found,
            "objectives_mentioned_count": objectives_count,
            "total_objectives": 6
        }
    
    def _calculate_taxonomy_quality(
        self,
        kpi_disclosure: Dict,
        objectives_analysis: Dict,
        dnsh_mentioned: bool,
        safeguards_mentioned: bool
    ) -> Dict[str, Any]:
        """Calculate quality score for taxonomy alignment disclosure."""
        
        # Scoring components (0-100)
        kpi_score = 100 if kpi_disclosure["all_three_kpis_disclosed"] else 50
        
        objectives_score = (
            objectives_analysis["objectives_mentioned_count"] / 6
        ) * 100
        
        dnsh_score = 100 if dnsh_mentioned else 0
        safeguards_score = 100 if safeguards_mentioned else 0
        
        # Weighted overall score
        overall_score = (
            kpi_score * 0.4 +           # 40% weight on KPI disclosure
            objectives_score * 0.3 +     # 30% weight on objectives
            dnsh_score * 0.15 +          # 15% weight on DNSH
            safeguards_score * 0.15      # 15% weight on safeguards
        )
        
        quality_level = (
            "EXCELLENT" if overall_score >= 85 else
            "GOOD" if overall_score >= 70 else
            "ADEQUATE" if overall_score >= 50 else
            "NEEDS_IMPROVEMENT"
        )
        
        return {
            "overall_score": round(overall_score, 1),
            "quality_level": quality_level,
            "breakdown": {
                "kpi_disclosure": kpi_score,
                "objectives_coverage": round(objectives_score, 1),
                "dnsh_coverage": dnsh_score,
                "safeguards_coverage": safeguards_score
            }
        }


# Singleton instance
taxonomy_service = TaxonomyService()

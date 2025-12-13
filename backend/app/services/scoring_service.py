"""
GreenGuard ESG Platform - Scoring Service
"""
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

INDUSTRY_BENCHMARKS = {
    "carbon_emissions": {"baseline": 1000, "target": 500, "unit": "tonnes CO2e"},
    "energy_usage": {"baseline": 50000, "target": 30000, "unit": "kWh"},
    "renewable_percentage": {"baseline": 20, "target": 50, "unit": "%"},
    "water_usage": {"baseline": 10000, "target": 5000, "unit": "m3"},
    "waste_recycled": {"baseline": 30, "target": 70, "unit": "%"}
}


class ScoringService:
    """Service for calculating ESG compliance scores."""
    
    def calculate_carbon_score(self, emissions: float) -> float:
        benchmark = INDUSTRY_BENCHMARKS["carbon_emissions"]
        if emissions <= benchmark["target"]:
            return 100.0
        elif emissions >= benchmark["baseline"]:
            return 30.0
        else:
            range_val = benchmark["baseline"] - benchmark["target"]
            progress = benchmark["baseline"] - emissions
            return 30.0 + (progress / range_val) * 70.0
    
    def calculate_energy_score(self, usage: float, renewable_pct: float = 0) -> float:
        energy_benchmark = INDUSTRY_BENCHMARKS["energy_usage"]
        energy_score = 50.0
        if usage <= energy_benchmark["target"]:
            energy_score = 80.0
        elif usage <= (energy_benchmark["baseline"] + energy_benchmark["target"]) / 2:
            energy_score = 60.0
        renewable_bonus = min(renewable_pct * 0.5, 20)
        return min(energy_score + renewable_bonus, 100.0)
    
    def calculate_taxonomy_score(self, metrics: Dict[str, Any], keywords: List[str]) -> float:
        score = 40.0
        if metrics.get("renewable_percentage", 0) > 30:
            score += 20
        if metrics.get("waste_recycled", 0) > 50:
            score += 15
        keyword_bonus = min(len(keywords) * 3, 15)
        score += keyword_bonus
        return min(score, 100.0)
    
    def calculate_overall_score(self, carbon: float, energy: float, taxonomy: float) -> float:
        return (
            carbon * settings.CARBON_WEIGHT +
            energy * settings.ENERGY_WEIGHT +
            taxonomy * settings.TAXONOMY_WEIGHT +
            60 * settings.WASTE_WEIGHT
        )
    
    def get_compliance_status(self, score: float) -> str:
        if score >= 80:
            return "Compliant"
        elif score >= 60:
            return "Partially Compliant"
        else:
            return "Non-Compliant"
    
    def generate_recommendations(self, metrics: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        recs = []
        if scores.get("carbon_score", 0) < 70:
            recs.append("Consider setting science-based carbon reduction targets")
        if scores.get("energy_efficiency_score", 0) < 70:
            recs.append("Increase renewable energy percentage to improve score")
        if scores.get("taxonomy_alignment_score", 0) < 70:
            recs.append("Align activities with EU Taxonomy for sustainable activities")
        return recs


scoring_service = ScoringService()

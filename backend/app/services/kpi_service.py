"""
GreenGuard ESG Platform - KPI Service
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

KPI_BENCHMARKS = {
    "manufacturing": {
        "co2_reduction": {"min": 10, "max": 30, "avg": 20, "target": 45, "unit": "%"},
        "energy_efficiency": {"min": 5, "max": 20, "avg": 12, "target": 30, "unit": "%"},
        "renewable_energy": {"min": 10, "max": 40, "avg": 25, "target": 60, "unit": "%"},
        "waste_recycling": {"min": 40, "max": 70, "avg": 55, "target": 85, "unit": "%"}
    },
    "financial_services": {
        "co2_reduction": {"min": 5, "max": 20, "avg": 12, "target": 35, "unit": "%"},
        "energy_efficiency": {"min": 10, "max": 30, "avg": 20, "target": 40, "unit": "%"},
        "renewable_energy": {"min": 20, "max": 50, "avg": 35, "target": 75, "unit": "%"}
    },
    "real_estate": {
        "co2_reduction": {"min": 15, "max": 35, "avg": 25, "target": 50, "unit": "%"},
        "energy_efficiency": {"min": 20, "max": 40, "avg": 30, "target": 55, "unit": "%"},
        "renewable_energy": {"min": 15, "max": 45, "avg": 30, "target": 70, "unit": "%"}
    },
    "transportation": {
        "co2_reduction": {"min": 10, "max": 25, "avg": 18, "target": 40, "unit": "%"},
        "energy_efficiency": {"min": 8, "max": 25, "avg": 16, "target": 35, "unit": "%"}
    },
    "technology": {
        "co2_reduction": {"min": 8, "max": 22, "avg": 15, "target": 40, "unit": "%"},
        "energy_efficiency": {"min": 15, "max": 35, "avg": 25, "target": 50, "unit": "%"},
        "renewable_energy": {"min": 30, "max": 60, "avg": 45, "target": 90, "unit": "%"}
    }
}


class KPIService:
    """Service for KPI benchmarking."""
    
    def get_sectors(self) -> list:
        return list(KPI_BENCHMARKS.keys())
    
    def get_metrics(self, sector: str) -> list:
        if sector in KPI_BENCHMARKS:
            return list(KPI_BENCHMARKS[sector].keys())
        return []
    
    def get_benchmark(self, sector: str, metric: str) -> Dict[str, Any]:
        if sector not in KPI_BENCHMARKS:
            return {}
        if metric not in KPI_BENCHMARKS[sector]:
            return {}
        
        data = KPI_BENCHMARKS[sector][metric]
        return {
            "sector": sector,
            "metric": metric,
            "baseline_range": {"min": data["min"], "max": data["max"]},
            "market_average": data["avg"],
            "ambitious_target": data["target"],
            "unit": data.get("unit", "%"),
            "recommendation": f"Target {data['target']}{data.get('unit', '%')} for {metric.replace('_', ' ')} to be industry-leading"
        }


kpi_service = KPIService()

"""
GreenGuard ESG Platform - ESG Mapping Service
"""
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

ESG_KEYWORDS = {
    "carbon": ["carbon", "co2", "emissions", "greenhouse", "ghg", "carbon footprint"],
    "energy": ["energy", "kwh", "electricity", "power consumption", "renewable"],
    "water": ["water", "wastewater", "water usage", "water consumption"],
    "waste": ["waste", "recycling", "recycled", "landfill", "circular economy"],
    "social": ["employees", "diversity", "safety", "health", "training"],
    "governance": ["board", "ethics", "compliance", "audit", "transparency"]
}

METRIC_PATTERNS = {
    "carbon_emissions": r"(?:carbon|co2|emissions?)[:\s]*(\d+[\d,\.]*)\s*(?:tonnes?|tons?|t|kg|mt)",
    "energy_usage": r"(?:energy|electricity|power)[:\s]*(\d+[\d,\.]*)\s*(?:kwh|mwh|gwh|gj)",
    "renewable_percentage": r"(?:renewable|clean energy)[:\s]*(\d+[\d,\.]*)\s*%",
    "water_usage": r"(?:water)[:\s]*(\d+[\d,\.]*)\s*(?:m3|liters?|gallons?|ml)",
    "waste_recycled": r"(?:recycl\w*|waste diverted)[:\s]*(\d+[\d,\.]*)\s*%?"
}


class ESGMappingService:
    """Service for extracting ESG metrics from text."""
    
    def extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extract ESG metrics from text using regex patterns."""
        metrics = {}
        text_lower = text.lower()
        
        for metric, pattern in METRIC_PATTERNS.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1).replace(",", ""))
                    metrics[metric] = value
                except ValueError:
                    pass
        
        return metrics
    
    def detect_keywords(self, text: str) -> List[str]:
        """Detect ESG-related keywords in text."""
        detected = []
        text_lower = text.lower()
        
        for category, keywords in ESG_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(f"{category}:{keyword}")
                    break
        
        return list(set(detected))
    
    def detect_red_flags(self, text: str) -> List[str]:
        """Detect potential red flags in ESG reports."""
        red_flags = []
        text_lower = text.lower()
        
        flag_patterns = [
            "not disclosed", "data unavailable", "no targets set",
            "pending verification", "significant increase", "non-compliance"
        ]
        
        for pattern in flag_patterns:
            if pattern in text_lower:
                red_flags.append(f"Red flag detected: '{pattern}'")
        
        return red_flags


esg_mapping_service = ESGMappingService()

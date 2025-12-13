"""
GreenGuard ESG Platform - Vendor Verification Service
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

APPROVED_GREEN_VENDORS = [
    {"name": "Tesla Energy", "category": "renewable_energy", "certification": "ISO 14001"},
    {"name": "Vestas", "category": "wind_energy", "certification": "B Corp"},
    {"name": "SunPower", "category": "solar", "certification": "ISO 14001"},
    {"name": "Schneider Electric", "category": "energy_efficiency", "certification": "SBTi"},
    {"name": "Siemens Gamesa", "category": "wind_energy", "certification": "ISO 14001"},
    {"name": "First Solar", "category": "solar", "certification": "EcoVadis Gold"},
    {"name": "ChargePoint", "category": "ev_infrastructure", "certification": "B Corp"}
]

NON_GREEN_KEYWORDS = [
    "coal", "fossil", "mining", "drilling", "fracking", "plastic manufacturer",
    "casino", "tobacco", "weapons", "gambling"
]


class VendorVerificationService:
    """Service for vendor verification."""
    
    def is_approved_vendor(self, vendor_name: str) -> bool:
        vendor_lower = vendor_name.lower()
        for vendor in APPROVED_GREEN_VENDORS:
            if vendor["name"].lower() in vendor_lower or vendor_lower in vendor["name"].lower():
                return True
        return False
    
    def has_red_flag_keywords(self, vendor_name: str, description: str = "") -> bool:
        combined = f"{vendor_name} {description}".lower()
        for keyword in NON_GREEN_KEYWORDS:
            if keyword in combined:
                return True
        return False
    
    def calculate_misuse_risk(self, vendor_name: str, amount: float, description: str = "") -> float:
        risk = 20.0
        if self.is_approved_vendor(vendor_name):
            risk -= 15
        if self.has_red_flag_keywords(vendor_name, description):
            risk += 50
        if amount > 1000000:
            risk += 15
        elif amount > 100000:
            risk += 5
        return max(0, min(100, risk))
    
    def verify_transaction(self, vendor_name: str, amount: float, description: str = "") -> Dict[str, Any]:
        is_approved = self.is_approved_vendor(vendor_name)
        has_red_flags = self.has_red_flag_keywords(vendor_name, description)
        misuse_risk = self.calculate_misuse_risk(vendor_name, amount, description)
        
        is_compliant = is_approved and not has_red_flags and misuse_risk < 40
        
        vendor_status = "approved" if is_approved else ("flagged" if has_red_flags else "unknown")
        
        recommendations = []
        if not is_approved:
            recommendations.append("Vendor not in approved green vendor list - consider verification")
        if has_red_flags:
            recommendations.append("Transaction contains potentially non-green keywords")
        if misuse_risk >= 40:
            recommendations.append("High risk score - additional review recommended")
        
        notes = f"Vendor status: {vendor_status}. Risk score: {misuse_risk:.1f}%"
        if has_red_flags:
            notes += ". Red flags detected."
        
        return {
            "is_green_compliant": is_compliant,
            "vendor_status": vendor_status,
            "misuse_risk_score": misuse_risk,
            "compliance_notes": notes,
            "recommendations": recommendations
        }


vendor_service = VendorVerificationService()

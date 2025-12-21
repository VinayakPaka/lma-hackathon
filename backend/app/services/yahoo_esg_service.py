"""
GreenGuard ESG Platform - Yahoo ESG Service
Retrieves ESG risk scores from Yahoo Finance for context (NOT ambition assessment).
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class YahooESGService:
    """
    Service for retrieving ESG risk scores from Yahoo Finance.
    
    IMPORTANT: These scores are used for RISK CONTEXT only, not ambition assessment.
    Yahoo ESG scores are derived from Sustainalytics and represent risk measures
    (lower score = better/lower risk).
    
    Usage Guidelines:
    - Use scores to flag elevated delivery risk
    - Do NOT use to determine target ambition
    - Always include caveat about score interpretation
    """
    
    ESG_RISK_THRESHOLDS = {
        "negligible": (0, 10),
        "low": (10, 20),
        "medium": (20, 30),
        "high": (30, 40),
        "severe": (40, 100)
    }
    
    def __init__(self):
        self._yf = None
    
    @property
    def yf(self):
        """Lazy import of yfinance."""
        if self._yf is None:
            try:
                import yfinance
                self._yf = yfinance
            except ImportError:
                logger.warning("yfinance not installed. ESG scores unavailable.")
                self._yf = None
        return self._yf
    
    def get_esg_scores(self, ticker: str) -> Dict[str, Any]:
        """
        Retrieve ESG risk scores from Yahoo Finance.
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL", "TCH.DE")
        
        Returns:
            Dictionary with ESG scores and risk interpretation
        """
        if not self.yf:
            return {
                "available": False,
                "error": "yfinance library not installed",
                "ticker": ticker
            }
        
        try:
            stock = self.yf.Ticker(ticker)
            sustainability = stock.sustainability
            
            if sustainability is None or sustainability.empty:
                return {
                    "available": False,
                    "error": "No ESG data available for this ticker",
                    "ticker": ticker
                }
            
            # Extract scores (Sustainalytics data)
            total_esg = self._safe_get(sustainability, "totalEsg")
            env_score = self._safe_get(sustainability, "environmentScore")
            social_score = self._safe_get(sustainability, "socialScore")
            gov_score = self._safe_get(sustainability, "governanceScore")
            controversy = self._safe_get(sustainability, "highestControversy")
            
            # Determine risk level
            risk_level = self._classify_risk(total_esg)
            delivery_risk = self._assess_delivery_risk(total_esg, controversy)
            
            return {
                "available": True,
                "ticker": ticker,
                "data_source": "Yahoo Finance (Sustainalytics)",
                "scores": {
                    "total_esg_risk": total_esg,
                    "environment_risk": env_score,
                    "social_risk": social_score,
                    "governance_risk": gov_score,
                    "controversy_level": controversy
                },
                "risk_level": risk_level,
                "delivery_risk_flag": delivery_risk["flagged"],
                "delivery_risk_reason": delivery_risk["reason"],
                "interpretation": self._get_interpretation(risk_level),
                "caveat": "These are RISK scores (lower = better). Used for context only, NOT for ambition assessment."
            }
            
        except Exception as e:
            logger.error(f"Yahoo ESG error for {ticker}: {e}")
            return {
                "available": False,
                "error": str(e),
                "ticker": ticker
            }
    
    def _safe_get(self, df, key: str) -> Optional[float]:
        """Safely extract value from sustainability DataFrame."""
        try:
            if key in df.index:
                val = df.loc[key]
                if hasattr(val, 'values'):
                    val = val.values[0]
                return float(val) if val is not None else None
            return None
        except:
            return None
    
    def _classify_risk(self, total_score: Optional[float]) -> str:
        """Classify overall ESG risk level."""
        if total_score is None:
            return "UNKNOWN"
        
        for level, (low, high) in self.ESG_RISK_THRESHOLDS.items():
            if low <= total_score < high:
                return level.upper()
        
        return "SEVERE" if total_score >= 40 else "UNKNOWN"
    
    def _assess_delivery_risk(
        self,
        total_score: Optional[float],
        controversy: Optional[float]
    ) -> Dict[str, Any]:
        """
        Assess if ESG scores indicate elevated delivery risk for sustainability targets.
        """
        risks = []
        
        if total_score and total_score >= 30:
            risks.append(f"High ESG risk score ({total_score:.1f}) may impact sustainability delivery")
        
        if controversy and controversy >= 4:
            risks.append(f"Significant controversy level ({controversy}) indicates reputational risk")
        
        return {
            "flagged": len(risks) > 0,
            "reason": "; ".join(risks) if risks else "ESG risk within acceptable range"
        }
    
    def _get_interpretation(self, risk_level: str) -> str:
        """Get human-readable interpretation of risk level."""
        interpretations = {
            "NEGLIGIBLE": "Strong ESG performance with minimal sustainability risk",
            "LOW": "Good ESG performance with limited risk factors",
            "MEDIUM": "Moderate ESG risk; sustainability targets achievable with governance",
            "HIGH": "Elevated ESG risk; may face challenges in sustainability delivery",
            "SEVERE": "Significant ESG concerns; heightened scrutiny recommended",
            "UNKNOWN": "ESG risk assessment not available"
        }
        return interpretations.get(risk_level, "ESG risk level unclear")
    
    def get_risk_flags(self, ticker: str) -> list:
        """
        Get a simple list of risk flags for inclusion in reports.
        """
        scores = self.get_esg_scores(ticker)
        flags = []
        
        if not scores.get("available"):
            return [{
                "severity": "INFO",
                "issue": "ESG risk data not available",
                "recommendation": "Consider manual ESG assessment"
            }]
        
        risk_level = scores.get("risk_level", "UNKNOWN")
        
        if risk_level in ["HIGH", "SEVERE"]:
            flags.append({
                "severity": "MEDIUM" if risk_level == "HIGH" else "HIGH",
                "issue": f"Elevated ESG risk ({scores['scores']['total_esg_risk']:.1f})",
                "recommendation": "Enhanced monitoring of sustainability commitments recommended"
            })
        
        if scores.get("delivery_risk_flag"):
            flags.append({
                "severity": "MEDIUM",
                "issue": scores.get("delivery_risk_reason"),
                "recommendation": "Assess company's capacity to deliver on sustainability targets"
            })
        
        return flags


# Singleton instance
yahoo_esg_service = YahooESGService()

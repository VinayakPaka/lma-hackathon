"""
GreenGuard ESG Platform - SBTi Data Service
Handles SBTi Excel data ingestion, peer selection, and percentile computation.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# Path to SBTi data files
SBTI_DATA_DIR = Path(__file__).parent.parent.parent / "resources" / "SBT'is Data"
COMPANIES_EXCEL = SBTI_DATA_DIR / "companies-excel.xlsx"
TARGETS_EXCEL = SBTI_DATA_DIR / "targets-excel.xlsx"


class SBTiDataService:
    """
    Service for loading and querying SBTi (Science Based Targets initiative) data.
    
    This service provides:
    - Excel data loading into memory/database
    - Peer company selection by sector/scope/region
    - Deterministic percentile computation
    - Confidence labeling based on peer pool size
    
    IMPORTANT: This service uses deterministic SQL/Pandas queries only.
    NO LLM/AI is used for peer selection or percentile calculations.
    """
    
    # Fallback industry benchmarks when SBTi data matching fails
    # Based on typical SBTi targets for common sectors
    FALLBACK_BENCHMARKS = {
        "default": {"median": 42.0, "p75": 50.0, "min": 25.0, "max": 65.0},
        "technology": {"median": 45.0, "p75": 55.0, "min": 30.0, "max": 70.0},
        "manufacturing": {"median": 40.0, "p75": 50.0, "min": 25.0, "max": 60.0},
        "energy": {"median": 35.0, "p75": 45.0, "min": 20.0, "max": 55.0},
        "financial": {"median": 46.0, "p75": 55.0, "min": 30.0, "max": 70.0},
        "healthcare": {"median": 40.0, "p75": 48.0, "min": 25.0, "max": 60.0},
        "automotive": {"median": 38.0, "p75": 48.0, "min": 22.0, "max": 58.0},
        "retail": {"median": 43.0, "p75": 52.0, "min": 28.0, "max": 62.0},
        "construction": {"median": 35.0, "p75": 45.0, "min": 20.0, "max": 55.0},
        "utilities": {"median": 38.0, "p75": 48.0, "min": 22.0, "max": 58.0},
        "industrial": {"median": 40.0, "p75": 50.0, "min": 25.0, "max": 60.0},
    }
    
    def __init__(self):
        self._companies_df: Optional[pd.DataFrame] = None
        self._targets_df: Optional[pd.DataFrame] = None
        self._loaded = False
    
    @property
    def companies_df(self) -> pd.DataFrame:
        """Lazy load companies DataFrame."""
        if self._companies_df is None:
            self._load_data()
        return self._companies_df
    
    @property
    def targets_df(self) -> pd.DataFrame:
        """Lazy load targets DataFrame."""
        if self._targets_df is None:
            self._load_data()
        return self._targets_df
    
    def _load_data(self) -> None:
        """
        Load SBTi Excel files into DataFrames.
        Called once on first access.
        """
        try:
            logger.info(f"Loading SBTi data from {SBTI_DATA_DIR}")
            
            # Load companies
            if COMPANIES_EXCEL.exists():
                self._companies_df = pd.read_excel(COMPANIES_EXCEL)
                # Standardize column names (they may vary)
                self._companies_df.columns = [
                    self._normalize_column_name(c) for c in self._companies_df.columns
                ]
                logger.info(f"Loaded {len(self._companies_df)} companies from SBTi dataset")
            else:
                logger.warning(f"Companies file not found: {COMPANIES_EXCEL}")
                self._companies_df = pd.DataFrame()
            
            # Load targets
            if TARGETS_EXCEL.exists():
                self._targets_df = pd.read_excel(TARGETS_EXCEL)
                self._targets_df.columns = [
                    self._normalize_column_name(c) for c in self._targets_df.columns
                ]
                logger.info(f"Loaded {len(self._targets_df)} targets from SBTi dataset")
            else:
                logger.warning(f"Targets file not found: {TARGETS_EXCEL}")
                self._targets_df = pd.DataFrame()
            
            self._loaded = True
            
        except Exception as e:
            logger.error(f"Error loading SBTi data: {e}")
            self._companies_df = pd.DataFrame()
            self._targets_df = pd.DataFrame()
    
    def _normalize_column_name(self, name: str) -> str:
        """Normalize column names to snake_case."""
        return str(name).lower().strip().replace(" ", "_").replace("-", "_")
    
    def get_available_sectors(self) -> List[str]:
        """Get list of unique sectors in the dataset."""
        if self.companies_df.empty:
            return []
        
        sector_col = self._find_column(self.companies_df, ["sector", "industry_sector", "industry"])
        if sector_col:
            return sorted(self.companies_df[sector_col].dropna().unique().tolist())
        return []
    
    def get_available_regions(self) -> List[str]:
        """Get list of unique regions in the dataset."""
        if self.companies_df.empty:
            return []
        
        region_col = self._find_column(self.companies_df, ["region", "location_region", "geographic_region"])
        if region_col:
            return sorted(self.companies_df[region_col].dropna().unique().tolist())
        return []
    
    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        """Find first matching column from list of candidates."""
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
            # Try partial match
            for col in df.columns:
                if candidate in col:
                    return col
        return None

    def _build_scope_mask(self, series: pd.Series, scope: str) -> pd.Series:
        """Robust scope matching for messy SBTi scope strings.

        Examples:
        - request "Scope 1+2" matches values containing "1" and "2" but not "3"
        - request "Scope 1+2+3" matches values containing "1", "2", and "3"
        - request "Scope 3" matches values containing "3"
        """
        scope_str = (scope or "").lower()
        requested_digits = {ch for ch in scope_str if ch in {"1", "2", "3"}}

        s = series.astype(str).str.lower()

        # If we can't detect digits, fall back to substring match.
        if not requested_digits:
            needle = scope_str.replace("+", "").strip()
            return s.str.contains(needle, na=False)

        mask = pd.Series(True, index=s.index)
        for d in sorted(requested_digits):
            mask &= s.str.contains(d, na=False)

        # If requester didn't include scope 3, exclude 1+2+3-type rows.
        if "3" not in requested_digits:
            mask &= ~s.str.contains("3", na=False)

        return mask
    
    def check_sbti_commitment(self, company_name: str) -> Dict[str, Any]:
        """
        Check if a company has SBTi commitment.
        
        Returns:
            Dictionary with commitment status and details
        """
        if self.companies_df.empty:
            return {
                "found": False,
                "error": "SBTi dataset not loaded"
            }
        
        name_col = self._find_column(self.companies_df, ["company_name", "company", "organization", "name"])
        if not name_col:
            return {"found": False, "error": "Could not find company name column"}
        
        # Search for company (case-insensitive partial match)
        matches = self.companies_df[
            self.companies_df[name_col].str.lower().str.contains(company_name.lower(), na=False)
        ]
        
        if matches.empty:
            return {
                "found": False,
                "searched_name": company_name,
                "total_companies_in_db": len(self.companies_df)
            }
        
        # Get first match
        match = matches.iloc[0]
        
        status_col = self._find_column(self.companies_df, ["status", "company_status", "target_status"])
        commitment_date_col = self._find_column(self.companies_df, ["date_joined", "commitment_date"])
        net_zero_col = self._find_column(self.companies_df, ["net_zero", "net_zero_committed"])
        
        return {
            "found": True,
            "company_name": match.get(name_col, company_name),
            "status": match.get(status_col) if status_col else None,
            "commitment_date": str(match.get(commitment_date_col)) if commitment_date_col else None,
            "net_zero_committed": bool(match.get(net_zero_col)) if net_zero_col else None,
            "match_count": len(matches)
        }
    
    def select_peer_group(
        self,
        sector: str,
        scope: str = "Scope 1+2",
        region: Optional[str] = None,
        target_year: Optional[int] = None,
        year_tolerance: int = 3
    ) -> Dict[str, Any]:
        """
        Select peer companies for benchmarking.
        
        Args:
            sector: Industry sector to match
            scope: Emission scope (Scope 1, Scope 2, Scope 1+2, Scope 3)
            region: Optional geographic region filter
            target_year: Optional target year for alignment
            year_tolerance: Years +/- for target year matching
        
        Returns:
            Dictionary with peer companies and match quality
        """
        if self.targets_df.empty or self.companies_df.empty:
            return {
                "peers": [],
                "peer_count": 0,
                "error": "SBTi dataset not loaded"
            }
        
        # Find relevant columns
        sector_col = self._find_column(self.companies_df, ["sector", "industry_sector"])
        region_col = self._find_column(self.companies_df, ["region", "location_region"])
        name_col = self._find_column(self.companies_df, ["company_name", "company", "name"])
        
        scope_col = self._find_column(self.targets_df, ["scope", "target_scope"])
        # SBTi targets file typically uses `target_value` for the reduction percentage.
        reduction_col = self._find_column(
            self.targets_df,
            [
                "target_value",
                "target_value_pct",
                "target_value_percent",
                "reduction",
                "reduction_percentage",
                "target_percentage",
            ],
        )
        target_year_col = self._find_column(self.targets_df, ["target_year", "year"])
        company_ref_col = self._find_column(self.targets_df, ["company_name", "company", "organization"])
        
        if not all([sector_col, scope_col, reduction_col]):
            return {
                "peers": [],
                "peer_count": 0,
                "error": "Required columns not found in dataset"
            }
        
        # Multi-strategy sector matching
        sector_lower = sector.lower()
        sector_matches = pd.DataFrame()
        match_strategy = "none"
        
        # Strategy 1: Exact match
        exact_match = self.companies_df[
            self.companies_df[sector_col].str.lower() == sector_lower
        ]
        if not exact_match.empty:
            sector_matches = exact_match
            match_strategy = "exact"
        
        # Strategy 2: Contains match
        if sector_matches.empty:
            contains_match = self.companies_df[
                self.companies_df[sector_col].str.lower().str.contains(sector_lower, na=False)
            ]
            if not contains_match.empty:
                sector_matches = contains_match
                match_strategy = "contains"
        
        # Strategy 3: Word-by-word match (for multi-word sectors) - BUT avoid overly generic words
        if sector_matches.empty:
            # Avoid matching on generic words like "industrial", "services", "manufacturing" alone
            # as these match too broadly (e.g., "Industrial Machinery" shouldn't match "Industrial Gases")
            generic_words = {'industrial', 'services', 'manufacturing', 'products', 'equipment', 'systems', 'solutions'}
            sector_words = [w for w in sector_lower.split() if len(w) > 4 and w not in generic_words]
            
            for word in sector_words:
                word_match = self.companies_df[
                    self.companies_df[sector_col].str.lower().str.contains(word, na=False)
                ]
                if not word_match.empty and len(word_match) < 200:  # Don't use if it matches too many
                    sector_matches = word_match
                    match_strategy = f"word:{word}"
                    logger.info(f"Matched sector using word '{word}' - found {len(word_match)} companies")
                    break
        
        # Strategy 4: Common sector aliases
        sector_aliases = {
            "software": ["technology", "it services", "information technology", "tech"],
            "technology": ["software", "it services", "information technology", "tech"],
            "banking": ["financial", "finance", "bank"],
            "finance": ["financial", "banking", "bank"],
            "energy": ["oil", "gas", "power", "utilities"],
            "automotive": ["automobile", "auto", "vehicle", "transportation"],
            "retail": ["consumer", "commerce"],
            "manufacturing": ["industrial", "production"],
            "healthcare": ["health", "pharmaceutical", "medical"],
            "construction": ["building", "infrastructure"],
        }
        
        if sector_matches.empty:
            aliases = sector_aliases.get(sector_lower, [])
            for alias in aliases:
                alias_match = self.companies_df[
                    self.companies_df[sector_col].str.lower().str.contains(alias, na=False)
                ]
                if not alias_match.empty:
                    sector_matches = alias_match
                    match_strategy = f"alias:{alias}"
                    break
        
        # Strategy 5: If still empty, use top sectors as fallback for demo
        if sector_matches.empty:
            # Get all unique sectors to help with debugging
            available_sectors = self.companies_df[sector_col].dropna().unique()[:20].tolist()
            return {
                "peers": [],
                "peer_count": 0,
                "match_quality": "no_match",
                "searched_sector": sector,
                "match_strategy": match_strategy,
                "available_sectors_sample": available_sectors
            }
        
        if region and region_col:
            region_filter = sector_matches[region_col].astype(str).str.lower().str.contains(region.lower(), na=False)
            if region_filter.any():
                sector_matches = sector_matches[region_filter]
        
        # Get company names for cross-referencing
        matched_companies = sector_matches[name_col].str.lower().tolist() if name_col else []
        
        # Filter targets by scope (robust matching)
        scope_filter = self._build_scope_mask(self.targets_df[scope_col], scope)
        target_matches = self.targets_df[scope_filter].copy()
        
        # If we have company references, filter to matched companies
        if company_ref_col and matched_companies:
            target_matches = target_matches[
                target_matches[company_ref_col].str.lower().isin(matched_companies)
            ]
        
        # Filter by target year if specified
        if target_year and target_year_col:
            year_filter = (
                (target_matches[target_year_col] >= target_year - year_tolerance) &
                (target_matches[target_year_col] <= target_year + year_tolerance)
            )
            if year_filter.any():
                target_matches = target_matches[year_filter]
        
        # Extract reduction percentages
        if target_matches.empty or reduction_col not in target_matches.columns:
            return {
                "peers": [],
                "peer_count": 0,
                "match_quality": "scope_not_found",
                "searched_sector": sector,
                "searched_scope": scope
            }
        
        # Build peer list
        peers = []
        for _, row in target_matches.iterrows():
            reduction_val = row.get(reduction_col)
            if pd.notna(reduction_val):
                try:
                    reduction_pct = float(str(reduction_val).replace("%", "").strip())

                    # SBTi `target_value` is commonly stored as a fraction (e.g., 0.42 == 42%).
                    # Normalize to percent for banker-facing outputs.
                    if 0 < reduction_pct <= 1.5:
                        reduction_pct = reduction_pct * 100.0

                    peers.append({
                        "company_name": row.get(company_ref_col, "Unknown"),
                        "reduction_percentage": reduction_pct,
                        "target_year": int(row.get(target_year_col)) if target_year_col and pd.notna(row.get(target_year_col)) else None,
                        "scope": row.get(scope_col, scope)
                    })
                except (ValueError, TypeError):
                    continue
        
        # Warn if peer group is very large (can indicate broad sector matching), but do not bias percentiles
        # by trimming to the most ambitious peers.
        if len(peers) > 1000:
            logger.warning(
                f"⚠️ LARGE PEER GROUP: {len(peers)} peers found for sector '{sector}'. "
                "Proceeding without trimming to preserve the percentile distribution."
            )
        
        # Determine match quality based on peer count and strategy
        if len(peers) >= 15 and match_strategy == "exact":
            match_quality = "exact"
        elif len(peers) >= 8:
            match_quality = "sector_only"
        elif len(peers) >= 5:
            match_quality = "broad"
        else:
            match_quality = "limited"
        
        return {
            "peers": peers,
            "peer_count": len(peers),
            "match_quality": match_quality,
            "match_strategy": match_strategy,
            "filters_applied": {
                "sector": sector,
                "scope": scope,
                "region": region,
                "target_year": target_year
            }
        }
    
    def compute_percentiles(
        self,
        sector: str,
        scope: str = "Scope 1+2",
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compute peer percentiles for a given sector and scope.
        
        This is a DETERMINISTIC calculation using numpy.
        No AI/LLM involved.
        
        Args:
            sector: Industry sector
            scope: Emission scope
            region: Optional region filter
        
        Returns:
            Dictionary with percentile statistics and confidence level
        """
        peer_result = self.select_peer_group(sector, scope, region)
        
        if peer_result["peer_count"] == 0:
            return {
                "error": "No peers found",
                "peer_count": 0,
                "confidence_level": "INSUFFICIENT",
                **peer_result
            }
        
        reductions = [p["reduction_percentage"] for p in peer_result["peers"]]
        
        if len(reductions) < 3:
            return {
                "error": "Insufficient peers for percentile calculation",
                "peer_count": len(reductions),
                "confidence_level": "INSUFFICIENT",
                "raw_values": reductions
            }
        
        # Compute percentiles using numpy
        arr = np.array(reductions)
        
        percentiles = {
            "peer_count": len(arr),
            "min": float(np.min(arr)),
            "p25": float(np.percentile(arr, 25)),
            "median": float(np.percentile(arr, 50)),
            "p75": float(np.percentile(arr, 75)),
            "max": float(np.max(arr)),
            "mean": float(np.mean(arr)),
            "std_dev": float(np.std(arr))
        }
        
        # Determine confidence level
        if len(arr) >= 15:
            confidence_level = "HIGH"
        elif len(arr) >= 8:
            confidence_level = "MEDIUM"
        elif len(arr) >= 5:
            confidence_level = "LOW"
        else:
            confidence_level = "INSUFFICIENT"
        
        return {
            "percentiles": percentiles,
            "confidence_level": confidence_level,
            "match_quality": peer_result["match_quality"],
            "filters_applied": peer_result["filters_applied"],
            "data_source": "SBTi Companies Database",
            "calculation_method": "numpy.percentile (deterministic)"
        }
    
    def classify_ambition(
        self,
        borrower_target: float,
        sector: str,
        scope: str = "Scope 1+2",
        sbti_aligned: bool = False,
        region: Optional[str] = None,
        peer_data: Optional[Dict[str, Any]] = None  # NEW: Accept pre-computed peer data
    ) -> Dict[str, Any]:
        """
        Classify target ambition using deterministic rules.
        
        Classification Logic:
        - WEAK: Below peer median
        - MARKET_STANDARD: >= median AND < 75th percentile
        - ABOVE_MARKET: >= 75th percentile
        - SCIENCE_ALIGNED: >= 75th percentile AND SBTi aligned
        
        Args:
            borrower_target: The company's reduction target (%)
            sector: Industry sector
            scope: Emission scope
            sbti_aligned: Whether company has SBTi validation
            region: Optional region filter
            peer_data: Pre-computed peer data from sector_matching_service (optional)
        
        Returns:
            Classification result with full context
        """
        percentiles = None
        confidence_level = "MEDIUM"
        match_quality = "exact"
        peer_count = 0
        
        # PRIORITY 1: Use pre-computed peer data if provided (from sector_matching_service)
        if peer_data and peer_data.get("peer_count", 0) >= 3 and "percentiles" in peer_data:
            percentiles = peer_data["percentiles"]
            peer_count = peer_data["peer_count"]
            confidence_level = peer_data.get("confidence_level", "HIGH")
            match_quality = "direct_from_targets"
            logger.info(f"Using pre-computed peer data: {peer_count} peers, confidence: {confidence_level}")
        
        # PRIORITY 2: Try compute_percentiles if no pre-computed data
        if percentiles is None:
            percentile_result = self.compute_percentiles(sector, scope, region)

            computed_peer_count = int((percentile_result.get("percentiles") or {}).get("peer_count") or 0)
            if "error" not in percentile_result and computed_peer_count >= 3:
                percentiles = percentile_result["percentiles"]
                peer_count = computed_peer_count
                confidence_level = percentile_result.get("confidence_level", "MEDIUM")
                match_quality = percentile_result.get("match_quality", "computed")
        
        # PRIORITY 3: Return error if no peer data available (NO FALLBACK!)
        if percentiles is None:
            logger.error(f"❌ No peer data available for sector: {sector}")
            logger.error(f"Please ensure SBTi data is loaded and sector name is correctly matched")
            return {
                "classification": "UNKNOWN",
                "rationale": f"No peer data available for sector '{sector}'. Cannot classify ambition without benchmarks.",
                "borrower_target": borrower_target,
                "peer_median": None,
                "peer_p75": None,
                "sbti_aligned": sbti_aligned,
                "confidence_level": "INSUFFICIENT",
                "peer_count": 0,
                "error": f"No peer data for sector '{sector}'",
                "filters_applied": {
                    "sector": sector,
                    "scope": scope,
                    "region": region
                }
            }
        
        median = percentiles["median"]
        p75 = percentiles["p75"]
        
        # Deterministic classification rules
        if borrower_target < median:
            base_class = "WEAK"
            rationale = f"Target of {borrower_target}% is below peer median of {median:.1f}%"
        elif borrower_target < p75:
            base_class = "MARKET_STANDARD"
            rationale = f"Target of {borrower_target}% is between median ({median:.1f}%) and 75th percentile ({p75:.1f}%)"
        else:
            base_class = "ABOVE_MARKET"
            rationale = f"Target of {borrower_target}% is at or above 75th percentile ({p75:.1f}%)"
        
        # Science alignment is a BONUS layer
        if base_class == "ABOVE_MARKET" and sbti_aligned:
            final_class = "SCIENCE_ALIGNED"
            rationale += " with SBTi validation"
        else:
            final_class = base_class
        
        return {
            "classification": final_class,
            "rationale": rationale,
            "borrower_target": borrower_target,
            "peer_median": median,
            "peer_p75": p75,
            "gap_to_median": round(borrower_target - median, 2),
            "gap_to_p75": round(borrower_target - p75, 2),
            "sbti_aligned": sbti_aligned,
            "percentile_rank": self._calculate_percentile_rank(borrower_target, percentiles),
            "confidence_level": confidence_level,
            "peer_count": peer_count,
            "match_quality": match_quality,
            "using_fallback": False,
            "filters_applied": {
                "sector": sector,
                "scope": scope,
                "region": region
            },
            "recommendation": self._generate_ambition_recommendation(
                final_class, borrower_target, median, p75
            )
        }
    
    def _get_fallback_benchmark(self, sector: str) -> Dict[str, float]:
        """
        Get fallback benchmark data for a sector.
        Uses keyword matching to find best sector match.
        """
        sector_lower = sector.lower()
        
        # Direct match
        for key in self.FALLBACK_BENCHMARKS:
            if key in sector_lower or sector_lower in key:
                return self.FALLBACK_BENCHMARKS[key]
        
        # Keyword matching for common sector terms
        sector_keywords = {
            "technology": ["tech", "software", "it", "digital", "electronics", "semiconductor"],
            "manufacturing": ["industrial", "production", "machinery", "equipment"],
            "energy": ["oil", "gas", "power", "utilities", "electric"],
            "financial": ["bank", "finance", "insurance", "investment"],
            "healthcare": ["health", "pharma", "medical", "biotech"],
            "automotive": ["auto", "vehicle", "transport", "mobility"],
            "retail": ["consumer", "commerce", "store", "shopping"],
            "construction": ["building", "infrastructure", "real estate"],
        }
        
        for sector_key, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in sector_lower:
                    return self.FALLBACK_BENCHMARKS.get(sector_key, self.FALLBACK_BENCHMARKS["default"])
        
        # Return default benchmarks
        return self.FALLBACK_BENCHMARKS["default"]
    
    def _calculate_percentile_rank(self, value: float, percentiles: Dict) -> int:
        """Calculate approximate percentile rank of a value."""
        if value <= percentiles["min"]:
            return 0
        if value >= percentiles["max"]:
            return 100
        if value < percentiles["p25"]:
            return int(25 * (value - percentiles["min"]) / (percentiles["p25"] - percentiles["min"]))
        if value < percentiles["median"]:
            return int(25 + 25 * (value - percentiles["p25"]) / (percentiles["median"] - percentiles["p25"]))
        if value < percentiles["p75"]:
            return int(50 + 25 * (value - percentiles["median"]) / (percentiles["p75"] - percentiles["median"]))
        return int(75 + 25 * (value - percentiles["p75"]) / (percentiles["max"] - percentiles["p75"]))
    
    def _generate_ambition_recommendation(
        self,
        classification: str,
        target: float,
        median: float,
        p75: float
    ) -> Dict[str, Any]:
        """Generate actionable recommendation based on classification."""
        if classification == "WEAK":
            return {
                "action": "INCREASE_TARGET",
                "suggested_minimum": round(median + 1, 1),
                "suggested_ambitious": round(p75, 1),
                "message": f"Consider increasing target to ≥{median + 1:.1f}% to reach market standard"
            }
        elif classification == "MARKET_STANDARD":
            return {
                "action": "CONSIDER_ENHANCEMENT",
                "suggested_ambitious": round(p75, 1),
                "message": f"Target is at market standard. Consider {p75:.1f}% for above-market positioning"
            }
        elif classification == "ABOVE_MARKET":
            return {
                "action": "CONSIDER_SBTI",
                "message": "Strong target. Consider SBTi validation for science-aligned classification"
            }
        else:  # SCIENCE_ALIGNED
            return {
                "action": "MAINTAIN",
                "message": "Excellent target with science-based validation"
            }
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded dataset."""
        return {
            "companies_count": len(self.companies_df) if not self.companies_df.empty else 0,
            "targets_count": len(self.targets_df) if not self.targets_df.empty else 0,
            "companies_file_exists": COMPANIES_EXCEL.exists(),
            "targets_file_exists": TARGETS_EXCEL.exists(),
            "sectors_available": len(self.get_available_sectors()),
            "regions_available": len(self.get_available_regions()),
            "data_loaded": self._loaded
        }


# Singleton instance
sbti_data_service = SBTiDataService()

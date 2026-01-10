"""
GreenGuard ESG Platform - Intelligent Sector Matching Service
Uses AI to research company industry and match to SBTi sectors.
"""
import logging
import json
import httpx
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)

# Path to SBTi data
SBTI_DATA_DIR = Path(__file__).parent.parent.parent / "resources" / "SBT'is Data"
TARGETS_EXCEL = SBTI_DATA_DIR / "targets-excel.xlsx"

# Complete list of 51 SBTi sectors
SBTI_SECTORS = [
    "Aerospace and Defense",
    "Air Freight Transportation and Logistics",
    "Air Transportation - Airlines",
    "Air Transportation - Airport Services",
    "Automobiles and Components",
    "Banks, Diverse Financials, Insurance",
    "Building Products",
    "Chemicals",
    "Construction Materials",
    "Construction and Engineering",
    "Consumer Durables, Household and Personal Products",
    "Containers and Packaging",
    "Education Services",
    "Electric Utilities and Independent Power Producers and Energy Traders (including Fossil, Alternative and Nuclear Energy)",
    "Electrical Equipment and Machinery",
    "Food Production - Agricultural Production",
    "Food Production - Animal Source Food Production",
    "Food and Beverage Processing",
    "Food and Staples Retailing",
    "Forest and Paper Products - Forestry, Timber, Pulp and Paper, Rubber",
    "Gas Utilities",
    "Ground Transportation - Highways and Railtracks",
    "Ground Transportation - Railroads Transportation",
    "Ground Transportation - Trucking Transportation",
    "Healthcare Equipment and Supplies",
    "Healthcare Providers and Services, and Healthcare Technology",
    "Homebuilding",
    "Hotels, Restaurants and Leisure, and Tourism Services",
    "Media",
    "Mining - Coal",
    "Mining - Iron, Aluminum, Other Metals",
    "Mining - Other (Rare Minerals, Precious Metals and Gems)",
    "Pharmaceuticals, Biotechnology and Life Sciences",
    "Professional Services",
    "Public Agencies",
    "Real Estate",
    "Retailing",
    "Semiconductors and Semiconductors Equipment",
    "Software and Services",
    "Solid Waste Management Utilities",
    "Specialized Consumer Services",
    "Specialized Financial Services, Consumer Finance, Insurance Brokerage Firms",
    "Technology Hardware and Equipment",
    "Telecommunication Services",
    "Textiles, Apparel, Footwear and Luxury Goods",
    "Tires",
    "Tobacco",
    "Trading Companies and Distributors, and Commercial Services and Supplies",
    "Water Transportation - Ports and Services",
    "Water Transportation - Water Transportation",
    "Water Utilities",
]


class SectorMatchingService:
    """
    Intelligent sector matching service that:
    1. Uses AI to research company industry
    2. Maps to the closest SBTi sector
    3. Returns sector for peer benchmarking
    """
    
    def __init__(self):
        self._targets_df: Optional[pd.DataFrame] = None
        self._loaded = False
    
    @property
    def targets_df(self) -> pd.DataFrame:
        """Lazy load targets DataFrame."""
        if self._targets_df is None:
            self._load_data()
        return self._targets_df
    
    def _load_data(self) -> None:
        """Load SBTi targets Excel file."""
        try:
            if TARGETS_EXCEL.exists():
                logger.info(f"Loading SBTi targets from {TARGETS_EXCEL}")
                self._targets_df = pd.read_excel(TARGETS_EXCEL)
                logger.info(f"Loaded {len(self._targets_df)} targets from SBTi dataset")
                self._loaded = True
            else:
                logger.warning(f"Targets file not found: {TARGETS_EXCEL}")
                self._targets_df = pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading SBTi data: {e}")
            self._targets_df = pd.DataFrame()
    
    def get_available_sectors(self) -> List[str]:
        """Return the list of available SBTi sectors."""
        return SBTI_SECTORS.copy()
    
    def lookup_company_in_sbti(self, company_name: str) -> Dict[str, Any]:
        """
        Look up company in SBTi targets data.
        If found, return sector directly from data (more reliable than AI matching).
        
        Args:
            company_name: Name of the company to search
            
        Returns:
            Dictionary with company info and sector if found
        """
        if self.targets_df.empty:
            logger.warning("SBTi data not loaded, cannot lookup company")
            return {"found": False, "error": "SBTi data not loaded"}
        
        # Case-insensitive search for company name
        company_lower = company_name.lower().strip()
        matches = self.targets_df[
            self.targets_df['company_name'].str.lower().str.strip().str.contains(
                company_lower, na=False
            )
        ]
        
        if not matches.empty:
            # Get the first match's sector
            first_match = matches.iloc[0]
            sector = first_match.get('sector', '')
            matched_name = first_match.get('company_name', company_name)
            
            # Count how many targets this company has
            target_count = len(matches)
            
            logger.info(f"Found company '{matched_name}' in SBTi data with sector '{sector}' ({target_count} targets)")
            
            return {
                "found": True,
                "company_name": matched_name,
                "sector": sector,
                "target_count": target_count,
                "source": "sbti_direct_lookup",
                "confidence": "HIGH"  # Direct lookup is always high confidence
            }
        
        logger.info(f"Company '{company_name}' not found in SBTi database")
        return {"found": False, "searched_name": company_name}
    
    def get_company_target_history(self, company_name: str) -> Dict[str, Any]:
        """
        Get comprehensive target history for a company from SBTi data.
        Used for trajectory analysis and credibility signal detection.
        
        Returns:
            - All targets (near-term, long-term, net-zero)
            - Base year and target year for each
            - Target values and types
            - Validation status
        """
        if self.targets_df.empty:
            return {"found": False, "error": "SBTi data not loaded"}
        
        # Case-insensitive search
        company_lower = company_name.lower().strip()
        matches = self.targets_df[
            self.targets_df['company_name'].str.lower().str.strip().str.contains(
                company_lower, na=False
            )
        ]
        
        if matches.empty:
            return {"found": False, "company_name": company_name}
        
        import pandas as pd
        
        # Extract target details
        targets = []
        for _, row in matches.iterrows():
            target_type = row.get('target', '')  # Near-term, Long-term, Net-zero
            if pd.isna(target_type) or not target_type:
                continue
                
            target_value = row.get('target_value')
            if pd.notna(target_value):
                # Convert decimal to percentage if needed
                if isinstance(target_value, (int, float)) and 0 < target_value <= 1:
                    target_value = target_value * 100
            else:
                target_value = None
            
            targets.append({
                "target_type": str(target_type),
                "scope": str(row.get('scope', '')),
                "target_value_pct": round(target_value, 1) if target_value else None,
                "base_year": int(row.get('base_year')) if pd.notna(row.get('base_year')) else None,
                "target_year": int(row.get('target_year')) if pd.notna(row.get('target_year')) else None,
                "status": row.get('status', ''),
                "validation_route": row.get('validation_route', ''),
                "target_classification": row.get('target_classification_short', '')
            })
        
        # Get company-level info from first row
        first = matches.iloc[0]
        company_info = {
            "company_name": first.get('company_name', company_name),
            "sector": first.get('sector', ''),
            "region": first.get('region', ''),
            "sbti_id": first.get('sbti_id', '')
        }
        
        # Check validation status (handle NaN values)
        # If company has Near-term or Long-term targets in SBTi database, they are considered validated
        # (SBTi only publishes validated targets)
        has_validated_targets = any(
            t.get('target_type', '').lower() in ['near-term', 'long-term', 'net-zero']
            for t in targets
        )
        
        # Also check explicit status field
        explicit_validation = any(
            isinstance(t.get('status'), str) and t.get('status', '').lower() in ['targets set', 'approved', 'validated']
            for t in targets
        )
        
        is_validated = has_validated_targets or explicit_validation
        
        # Determine near-term and long-term targets
        near_term_targets = [t for t in targets if 'near' in t.get('target_type', '').lower()]
        long_term_targets = [t for t in targets if 'long' in t.get('target_type', '').lower()]
        net_zero_targets = [t for t in targets if 'net-zero' in t.get('target_type', '').lower() or 'net zero' in t.get('target_type', '').lower()]
        
        # Calculate trajectory info if we have both baseline and target
        trajectory_info = None
        if near_term_targets:
            nt = near_term_targets[0]
            if nt.get('base_year') and nt.get('target_year') and nt.get('target_value_pct'):
                years = nt['target_year'] - nt['base_year']
                if years > 0:
                    annual_rate = nt['target_value_pct'] / years
                    trajectory_info = {
                        "base_year": nt['base_year'],
                        "target_year": nt['target_year'],
                        "total_reduction_pct": nt['target_value_pct'],
                        "annual_reduction_rate": round(annual_rate, 2),
                        "years_to_target": years,
                        "scope": nt['scope']
                    }
        
        logger.info(f"Extracted {len(targets)} targets for {company_name} (validated: {is_validated})")
        
        return {
            "found": True,
            "company_info": company_info,
            "is_sbti_validated": is_validated,
            "target_count": len(targets),
            "near_term_targets": near_term_targets,
            "long_term_targets": long_term_targets,
            "net_zero_targets": net_zero_targets,
            "all_targets": targets,
            "trajectory_info": trajectory_info,
            "source": "sbti_database"
        }
    
    async def research_company_sector(
        self,
        company_name: str,
        user_provided_industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determine the best SBTi sector match for a company.
        
        Priority:
        1. Direct lookup in SBTi data (most reliable)
        2. AI research via Perplexity
        3. Keyword-based fallback
        
        Args:
            company_name: Name of the company to research
            user_provided_industry: Optional industry provided by user
            
        Returns:
            Dictionary with matched sector and confidence
        """
        # STEP 1: Try direct lookup in SBTi data first (user's great idea!)
        sbti_lookup = self.lookup_company_in_sbti(company_name)
        if sbti_lookup.get("found"):
            logger.info(f"Using sector from direct SBTi lookup: {sbti_lookup['sector']}")
            return {
                "success": True,
                "company_name": sbti_lookup.get("company_name", company_name),
                "matched_sector": sbti_lookup["sector"],
                "researched_industry": sbti_lookup["sector"],  # Same as sector for direct lookup
                "confidence": "HIGH",
                "reasoning": f"Company found directly in SBTi database with {sbti_lookup.get('target_count', 0)} targets",
                "source": "sbti_direct_lookup"
            }
        
        # STEP 2: AI research for companies not in SBTi database
        try:
            # Build the research prompt
            sectors_list = "\n".join([f"- {s}" for s in SBTI_SECTORS])
            
            prompt = f"""You are an industry classification expert. Research the company "{company_name}" and determine which SBTi (Science Based Targets initiative) sector best matches their primary business.

{"User indicated industry: " + user_provided_industry if user_provided_industry else ""}

Available SBTi sectors (you MUST choose from this exact list):
{sectors_list}

Research the company and respond with ONLY valid JSON in this exact format:
{{
    "company_name": "{company_name}",
    "researched_industry": "Primary industry/business of the company based on research",
    "matched_sbti_sector": "Exact sector name from the list above",
    "confidence": "HIGH|MEDIUM|LOW",
    "reasoning": "Brief explanation of why this sector was chosen"
}}

Important:
1. The matched_sbti_sector MUST be exactly one sector from the list above
2. Choose the most specific matching sector
3. If company spans multiple sectors, choose their PRIMARY business sector
"""
            
            result = await self._call_perplexity_for_research(prompt)
            
            if result:
                # Validate the sector is in our list
                matched_sector = result.get("matched_sbti_sector", "")
                if matched_sector not in SBTI_SECTORS:
                    # Find closest match
                    matched_sector = self._find_closest_sector(matched_sector)
                    result["matched_sbti_sector"] = matched_sector
                    result["sector_corrected"] = True
                
                return {
                    "success": True,
                    "company_name": company_name,
                    "matched_sector": result.get("matched_sbti_sector"),
                    "researched_industry": result.get("researched_industry"),
                    "confidence": result.get("confidence", "MEDIUM"),
                    "reasoning": result.get("reasoning"),
                    "source": "ai_research"
                }
            else:
                # Fallback to basic matching
                return self._fallback_sector_match(company_name, user_provided_industry)
                
        except Exception as e:
            logger.error(f"Error researching company sector: {e}")
            return self._fallback_sector_match(company_name, user_provided_industry)
    
    async def _call_perplexity_for_research(self, prompt: str) -> Optional[Dict]:
        """Call Perplexity API for company research."""
        try:
            api_key = settings.PERPLEXITY_API_KEY
            if not api_key:
                logger.warning("Perplexity API key not configured")
                return None
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar",
                        "messages": [
                            {"role": "system", "content": "You are a company research expert. Always respond with valid JSON only."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "max_tokens": 1000
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Parse JSON from response
                    # Handle potential markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    return json.loads(content.strip())
                else:
                    logger.error(f"Perplexity API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Perplexity research call failed: {e}")
            return None
    
    def _find_closest_sector(self, sector: str) -> str:
        """Find closest matching sector from the list."""
        sector_lower = sector.lower()
        
        # Try exact substring match
        for s in SBTI_SECTORS:
            if sector_lower in s.lower() or s.lower() in sector_lower:
                return s
        
        # Try word matching
        sector_words = set(sector_lower.split())
        best_match = SBTI_SECTORS[0]
        best_score = 0
        
        for s in SBTI_SECTORS:
            s_words = set(s.lower().replace("-", " ").replace(",", " ").split())
            common = len(sector_words & s_words)
            if common > best_score:
                best_score = common
                best_match = s
        
        return best_match
    
    def _fallback_sector_match(
        self,
        company_name: str,
        user_industry: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback sector matching using keyword rules."""
        logger.warning(f"Using fallback sector matching for {company_name}")
        
        search_text = f"{company_name} {user_industry or ''}".lower()
        
        # Keyword to sector mapping
        keyword_mapping = {
            "software": "Software and Services",
            "tech": "Technology Hardware and Equipment",
            "bank": "Banks, Diverse Financials, Insurance",
            "finance": "Banks, Diverse Financials, Insurance",
            "insurance": "Banks, Diverse Financials, Insurance",
            "auto": "Automobiles and Components",
            "car": "Automobiles and Components",
            "vehicle": "Automobiles and Components",
            "pharma": "Pharmaceuticals, Biotechnology and Life Sciences",
            "biotech": "Pharmaceuticals, Biotechnology and Life Sciences",
            "health": "Healthcare Providers and Services, and Healthcare Technology",
            "hospital": "Healthcare Providers and Services, and Healthcare Technology",
            "electric": "Electrical Equipment and Machinery",
            "energy": "Electric Utilities and Independent Power Producers and Energy Traders (including Fossil, Alternative and Nuclear Energy)",
            "utility": "Electric Utilities and Independent Power Producers and Energy Traders (including Fossil, Alternative and Nuclear Energy)",
            "oil": "Electric Utilities and Independent Power Producers and Energy Traders (including Fossil, Alternative and Nuclear Energy)",
            "gas": "Gas Utilities",
            "chemical": "Chemicals",
            "retail": "Retailing",
            "food": "Food and Beverage Processing",
            "beverage": "Food and Beverage Processing",
            "telecom": "Telecommunication Services",
            "media": "Media",
            "construction": "Construction and Engineering",
            "build": "Building Products",
            "real estate": "Real Estate",
            "property": "Real Estate",
            "aerospace": "Aerospace and Defense",
            "defense": "Aerospace and Defense",
            "airline": "Air Transportation - Airlines",
            "semiconductor": "Semiconductors and Semiconductors Equipment",
            "chip": "Semiconductors and Semiconductors Equipment",
            "mining": "Mining - Iron, Aluminum, Other Metals",
            "metal": "Mining - Iron, Aluminum, Other Metals",
            "hotel": "Hotels, Restaurants and Leisure, and Tourism Services",
            "restaurant": "Hotels, Restaurants and Leisure, and Tourism Services",
            "tourism": "Hotels, Restaurants and Leisure, and Tourism Services",
            "textile": "Textiles, Apparel, Footwear and Luxury Goods",
            "apparel": "Textiles, Apparel, Footwear and Luxury Goods",
            "fashion": "Textiles, Apparel, Footwear and Luxury Goods",
            "shipping": "Water Transportation - Water Transportation",
            "logistics": "Air Freight Transportation and Logistics",
            "transport": "Ground Transportation - Trucking Transportation",
            "truck": "Ground Transportation - Trucking Transportation",
            "rail": "Ground Transportation - Railroads Transportation",
            "education": "Education Services",
            "consulting": "Professional Services",
            "professional": "Professional Services",
            "packaging": "Containers and Packaging",
            "paper": "Forest and Paper Products - Forestry, Timber, Pulp and Paper, Rubber",
            "water": "Water Utilities",
            "waste": "Solid Waste Management Utilities",
        }
        
        # Find first matching keyword
        for keyword, sector in keyword_mapping.items():
            if keyword in search_text:
                return {
                    "success": True,
                    "company_name": company_name,
                    "matched_sector": sector,
                    "researched_industry": user_industry or "Unknown",
                    "confidence": "LOW",
                    "reasoning": f"Matched based on keyword '{keyword}' (fallback method)",
                    "source": "keyword_fallback"
                }
        
        # Default to a generic sector
        return {
            "success": True,
            "company_name": company_name,
            "matched_sector": "Professional Services",  # Generic default
            "researched_industry": user_industry or "Unknown",
            "confidence": "LOW",
            "reasoning": "No specific match found, using generic sector",
            "source": "default_fallback"
        }
    
    def get_peer_targets_for_sector(
        self,
        sector: str,
        scope: str = "1+2"
    ) -> Dict[str, Any]:
        """
        Get peer target values for a specific sector.
        
        Args:
            sector: SBTi sector name
            scope: Target scope (1, 2, 1+2, 3, etc.)
            
        Returns:
            Dictionary with peer targets and statistics
        """
        if self.targets_df.empty:
            return {"error": "SBTi data not loaded", "peer_count": 0}
        
        df = self.targets_df
        
        # Filter by sector
        sector_mask = df['sector'].str.lower() == sector.lower()
        sector_df = df[sector_mask]
        
        if sector_df.empty:
            # Try partial match
            sector_mask = df['sector'].str.lower().str.contains(sector.lower().split()[0], na=False)
            sector_df = df[sector_mask]
        
        if sector_df.empty:
            return {
                "sector": sector,
                "peer_count": 0,
                "error": "No peers found for this sector"
            }
        
        # Filter by scope - properly handle SBTi scope format
        # SBTi uses: '1+2', '1+2+3', 1, 2, 3, '1+3' (mixed int/string)
        # User input might be: 'Scope 1+2', '1+2', 'Scope 1', etc.
        scope_normalized = str(scope).replace("Scope ", "").strip()  # "Scope 1+2" -> "1+2"
        
        # Convert all scopes to string for comparison
        sector_df_scopes = sector_df['scope'].astype(str).str.strip()
        
        # Try exact match first
        scope_mask = sector_df_scopes == scope_normalized
        
        # If no exact match, try matching individual scopes (e.g., "1+2" should match rows with scope 1, 2, or 1+2)
        if not scope_mask.any() and "+" in scope_normalized:
            individual_scopes = scope_normalized.split("+")
            scope_mask = sector_df_scopes.isin(individual_scopes + [scope_normalized])
        
        # If still no match, try contains as fallback
        if not scope_mask.any():
            # Remove + for contains check (e.g., "12" should match "1+2")
            scope_digits = scope_normalized.replace("+", "")
            scope_mask = sector_df_scopes.str.replace("+", "", regex=False).str.contains(scope_digits, na=False)
        
        filtered_df = sector_df[scope_mask] if scope_mask.any() else sector_df
        
        logger.info(f"Scope filtering: '{scope}' -> '{scope_normalized}', matched {len(filtered_df)} rows")
        
        # Get target values (they vary in format, need to parse)
        target_values = []
        for _, row in filtered_df.iterrows():
            try:
                val = row.get('target_value')
                if pd.notna(val):
                    # Handle percentage strings like "42%" or numeric values
                    if isinstance(val, str):
                        val = float(val.replace('%', '').strip())
                    else:
                        val = float(val)
                    
                    # Handle both decimal format (0.42) and percentage format (42%)
                    # SBTi data sometimes stores as decimals
                    if 0 < val <= 1:
                        # Likely decimal format, convert to percentage
                        val = val * 100
                    
                    if 0 < val <= 100:  # Reasonable percentage range
                        target_values.append(val)
            except (ValueError, TypeError):
                continue
        
        if len(target_values) < 3:
            return {
                "sector": sector,
                "scope": scope,
                "peer_count": len(target_values),
                "error": "Insufficient data for percentile calculation"
            }
        
        import numpy as np
        arr = np.array(target_values)
        
        return {
            "sector": sector,
            "scope": scope,
            "peer_count": len(arr),
            "companies_in_sector": len(sector_df['company_name'].unique()),
            "percentiles": {
                "min": float(np.min(arr)),
                "p25": float(np.percentile(arr, 25)),
                "median": float(np.percentile(arr, 50)),
                "p75": float(np.percentile(arr, 75)),
                "max": float(np.max(arr)),
                "mean": float(np.mean(arr)),
                "std_dev": float(np.std(arr))
            },
            "confidence_level": "HIGH" if len(arr) >= 15 else "MEDIUM" if len(arr) >= 8 else "LOW"
        }


# Singleton instance
sector_matching_service = SectorMatchingService()

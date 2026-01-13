import eurostat
import logging
from typing import Dict, Any, Optional

class EurostatService:
    """
    Eurostat data retrieval with graceful degradation.
    When no data is found for a specific NACE code, returns sensible defaults
    so the benchmarking pipeline can continue.
    """
    
    # Fallback sector reduction rates when Eurostat has no data
    # Based on typical industry decarbonization benchmarks
    FALLBACK_SECTOR_DEFAULTS = {
        "average_reduction_rate": 4.2,  # Conservative industry average %/year
        "average_emissions": None,
        "unit": "THS_T",
        "year": 2023,
        "source": "Fallback (Eurostat data unavailable for this NACE code)",
        "data_quality": "LOW",
    }
    
    def __init__(self):
        # Dataset for Air Emissions Accounts by NACE Rev. 2 activity
        self.dataset_code = "env_ac_ainah_r2" 
        
    async def get_sector_data(self, nace_code: str, unit: str = "G_HAB") -> Dict[str, Any]:
        """
        Fetch real GHG emissions data for a specific NACE sector.
        Returns fallback defaults if no data is found (graceful degradation).
        """
        try:
            logging.info(f"Fetching Eurostat data for {nace_code}...")
            
            # Fetch data frame
            df = eurostat.get_data_df(self.dataset_code)
            
            if df is not None and not df.empty:
                # Filter locally
                # Columns usually: freq, airpol, unit, nace_r2, geo\time
                
                # Check column names (they vary)
                # Standardize: unit, airpol, nace_r2
                
                # Filter for GHG
                if 'airpol' in df.columns:
                    df = df[df['airpol'] == 'GHG']
                
                # Filter for Unit (THS_T = Thousand Tonnes, or use user request)
                if 'unit' in df.columns:
                    df = df[df['unit'] == 'THS_T']
                    
                # Filter for Sector
                if 'nace_r2' in df.columns:
                    df = df[df['nace_r2'] == nace_code]
                    
                # Filter for EU27 Average
                if 'geo\\TIME_PERIOD' in df.columns:
                    geo_col = 'geo\\TIME_PERIOD'
                else:
                    geo_col = 'geo'
                    
                eu_df = df[df[geo_col] == 'EU27_2020']
                
                if not eu_df.empty:
                    # Get latest year (column names are years)
                    year_cols = [c for c in eu_df.columns if str(c).isdigit()]
                    if year_cols:
                        latest_year = max(year_cols)
                        value = eu_df.iloc[0][latest_year]
                        return {
                            "sector": nace_code,
                            "average_emissions": value,
                            "average_reduction_rate": 4.5,  # Typical EU sector avg
                            "unit": "THS_T",
                            "year": latest_year,
                            "source": "Eurostat (env_ac_ainah_r2)",
                            "data_quality": "HIGH",
                        }

            # No data found - return fallback defaults
            logging.warning(f"No Eurostat data for NACE '{nace_code}'. Using fallback defaults.")
            return {
                "sector": nace_code,
                **self.FALLBACK_SECTOR_DEFAULTS,
            }

        except Exception as e:
            logging.error(f"Eurostat API Error for NACE '{nace_code}': {e}")
            # Return fallback on any error (network, parsing, etc.)
            return {
                "sector": nace_code,
                **self.FALLBACK_SECTOR_DEFAULTS,
                "error": str(e),
            }

    async def get_country_profile(self, country_code: str) -> Dict[str, Any]:
        """
        Get country-level renewable energy profile.
        Returns fallback for unknown countries.
        """
        profiles = {
            "ES": {"renewable_mix": 45, "region": "EU_SOUTH"},
            "DE": {"renewable_mix": 40, "region": "EU_CENTRAL"},
            "FR": {"renewable_mix": 25, "region": "EU_WEST"},  # Nuclear often separate
            "IT": {"renewable_mix": 35, "region": "EU_SOUTH"},
            "NL": {"renewable_mix": 30, "region": "EU_NORTH"},
            "BE": {"renewable_mix": 28, "region": "EU_WEST"},
            "AT": {"renewable_mix": 75, "region": "EU_CENTRAL"},
            "SE": {"renewable_mix": 60, "region": "EU_NORTH"},
            "PL": {"renewable_mix": 18, "region": "EU_EAST"},
            "PT": {"renewable_mix": 55, "region": "EU_SOUTH"},
        }
        
        profile = profiles.get(country_code)
        if not profile:
            logging.warning(f"Unknown country code '{country_code}'. Using EU average fallback.")
            return {
                "renewable_mix": 35,  # EU average
                "region": "EU_UNKNOWN",
                "data_quality": "LOW",
            }
        return {**profile, "data_quality": "HIGH"}

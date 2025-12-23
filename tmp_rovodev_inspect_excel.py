"""
Inspect SBTi Excel files to understand the data structure
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

try:
    import pandas as pd
    print("✓ pandas imported successfully")
    
    SBTI_DATA_DIR = Path("backend/resources/SBT'is Data")
    COMPANIES_EXCEL = SBTI_DATA_DIR / "companies-excel.xlsx"
    TARGETS_EXCEL = SBTI_DATA_DIR / "targets-excel.xlsx"
    
    print(f"\n=== FILE CHECK ===")
    print(f"Companies file: {COMPANIES_EXCEL}")
    print(f"  Exists: {COMPANIES_EXCEL.exists()}")
    print(f"Targets file: {TARGETS_EXCEL}")
    print(f"  Exists: {TARGETS_EXCEL.exists()}")
    
    if COMPANIES_EXCEL.exists():
        print(f"\n=== READING COMPANIES FILE ===")
        companies_df = pd.read_excel(COMPANIES_EXCEL)
        print(f"Shape: {companies_df.shape}")
        print(f"\nColumns ({len(companies_df.columns)}):")
        for i, col in enumerate(companies_df.columns, 1):
            print(f"  {i}. {col}")
        
        # Find sector column
        sector_cols = [col for col in companies_df.columns if 'sector' in col.lower() or 'industry' in col.lower()]
        print(f"\n=== SECTOR COLUMNS ===")
        print(f"Found {len(sector_cols)} sector-related columns:")
        for col in sector_cols:
            print(f"  - {col}")
            unique_count = companies_df[col].nunique()
            print(f"    Unique values: {unique_count}")
            print(f"    Sample values:")
            for val in companies_df[col].dropna().unique()[:15]:
                count = len(companies_df[companies_df[col] == val])
                print(f"      • {val} ({count} companies)")
        
        # Check for Siemens
        print(f"\n=== SEARCHING FOR SIEMENS ===")
        name_cols = [col for col in companies_df.columns if 'company' in col.lower() or 'name' in col.lower() or 'organization' in col.lower()]
        print(f"Name columns found: {name_cols}")
        
        for name_col in name_cols:
            siemens_matches = companies_df[companies_df[name_col].str.contains('Siemens', case=False, na=False)]
            if len(siemens_matches) > 0:
                print(f"\nFound {len(siemens_matches)} Siemens entries in column '{name_col}':")
                for idx, row in siemens_matches.head(5).iterrows():
                    print(f"  - {row[name_col]}")
                    if sector_cols:
                        print(f"    Sector: {row[sector_cols[0]]}")
        
        # Check for "Industrial" in sectors
        if sector_cols:
            main_sector_col = sector_cols[0]
            print(f"\n=== INDUSTRIAL SECTOR MATCHES ===")
            industrial = companies_df[companies_df[main_sector_col].str.contains('Industrial', case=False, na=False)]
            print(f"Found {len(industrial)} companies with 'Industrial' in sector")
            if len(industrial) > 0:
                print("Unique industrial sectors:")
                for sector in industrial[main_sector_col].unique()[:10]:
                    count = len(industrial[industrial[main_sector_col] == sector])
                    print(f"  • {sector} ({count} companies)")
    
    if TARGETS_EXCEL.exists():
        print(f"\n\n=== READING TARGETS FILE ===")
        targets_df = pd.read_excel(TARGETS_EXCEL)
        print(f"Shape: {targets_df.shape}")
        print(f"\nColumns ({len(targets_df.columns)}):")
        for i, col in enumerate(targets_df.columns[:20], 1):
            print(f"  {i}. {col}")
        
        # Find key columns
        scope_cols = [col for col in targets_df.columns if 'scope' in col.lower()]
        reduction_cols = [col for col in targets_df.columns if 'reduction' in col.lower() or 'target' in col.lower()]
        
        print(f"\nScope columns: {scope_cols}")
        if scope_cols:
            print(f"Unique scopes:")
            for scope in targets_df[scope_cols[0]].dropna().unique()[:10]:
                count = len(targets_df[targets_df[scope_cols[0]] == scope])
                print(f"  • {scope} ({count} targets)")
        
        print(f"\nReduction/Target columns: {reduction_cols[:5]}")

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Please install pandas: pip install pandas openpyxl")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

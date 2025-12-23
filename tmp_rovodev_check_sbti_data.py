"""
Quick script to check what's in the SBTi Excel files
"""
import pandas as pd
from pathlib import Path

SBTI_DATA_DIR = Path("backend/resources/SBT'is Data")
COMPANIES_EXCEL = SBTI_DATA_DIR / "companies-excel.xlsx"
TARGETS_EXCEL = SBTI_DATA_DIR / "targets-excel.xlsx"

print(f"Checking SBTi data files...")
print(f"Companies file exists: {COMPANIES_EXCEL.exists()}")
print(f"Targets file exists: {TARGETS_EXCEL.exists()}")

if COMPANIES_EXCEL.exists():
    try:
        companies_df = pd.read_excel(COMPANIES_EXCEL)
        print(f"\n=== COMPANIES FILE ===")
        print(f"Total companies: {len(companies_df)}")
        print(f"Columns: {companies_df.columns.tolist()}")
        
        # Try to find sector column
        sector_cols = [col for col in companies_df.columns if 'sector' in col.lower() or 'industry' in col.lower()]
        print(f"\nSector-related columns: {sector_cols}")
        
        if sector_cols:
            sector_col = sector_cols[0]
            print(f"\nUnique sectors (first 30):")
            unique_sectors = companies_df[sector_col].dropna().unique()
            for sector in unique_sectors[:30]:
                count = len(companies_df[companies_df[sector_col] == sector])
                print(f"  - {sector} ({count} companies)")
            
            # Check for "Industrial Conglomerates" or similar
            industrial = companies_df[companies_df[sector_col].str.contains("Industrial", case=False, na=False)]
            print(f"\n'Industrial' related companies: {len(industrial)}")
            
            # Check for Siemens
            siemens = companies_df[companies_df.apply(lambda x: 'siemens' in str(x).lower(), axis=1).any(axis=1)]
            print(f"Siemens-related companies: {len(siemens)}")
            if len(siemens) > 0:
                print("\nSiemens entries:")
                print(siemens.head())
        
    except Exception as e:
        print(f"Error reading companies file: {e}")

if TARGETS_EXCEL.exists():
    try:
        targets_df = pd.read_excel(TARGETS_EXCEL)
        print(f"\n=== TARGETS FILE ===")
        print(f"Total targets: {len(targets_df)}")
        print(f"Columns: {targets_df.columns.tolist()}")
        
        # Check scope column
        scope_cols = [col for col in targets_df.columns if 'scope' in col.lower()]
        if scope_cols:
            print(f"\nUnique scopes:")
            print(targets_df[scope_cols[0]].unique()[:10])
            
    except Exception as e:
        print(f"Error reading targets file: {e}")

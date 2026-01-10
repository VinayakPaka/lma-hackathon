"""Script to explore SBTi Excel data structure"""
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent / "resources" / "SBT'is Data"
TARGETS_FILE = DATA_DIR / "targets-excel.xlsx"
COMPANIES_FILE = DATA_DIR / "companies-excel.xlsx"

print(f"Looking for files in: {DATA_DIR}")
print(f"Files exist: targets={TARGETS_FILE.exists()}, companies={COMPANIES_FILE.exists()}")

if TARGETS_FILE.exists():
    df = pd.read_excel(TARGETS_FILE)
    print("\n=== TARGETS FILE ===")
    print(f"Columns: {list(df.columns)}")
    print(f"\nTotal rows: {len(df)}")
    
    # Find sector column
    sector_cols = [c for c in df.columns if 'sector' in c.lower()]
    print(f"\nSector columns: {sector_cols}")
    
    if sector_cols:
        print(f"\nUnique sectors ({len(df[sector_cols[0]].dropna().unique())}):")
        for s in sorted(df[sector_cols[0]].dropna().unique())[:20]:
            print(f"  - {s}")
    
    # Check for Siemens
    name_cols = [c for c in df.columns if 'company' in c.lower() or 'name' in c.lower()]
    print(f"\nName columns: {name_cols}")
    if name_cols:
        siemens = df[df[name_cols[0]].str.contains('Siemens', case=False, na=False)]
        print(f"\nSiemens rows: {len(siemens)}")
        if len(siemens) > 0:
            print("\nSiemens details:")
            cols_to_show = ['company_name', 'sector', 'scope', 'target_value', 'target_year', 'target']
            existing_cols = [c for c in cols_to_show if c in siemens.columns]
            print(siemens[existing_cols].head(10).to_string())
    
    # Check target value samples
    print("\n=== TARGET VALUE SAMPLES ===")
    print(df['target_value'].dropna().head(20).tolist())
    
    # Check scope column
    scope_cols = [c for c in df.columns if 'scope' in c.lower()]
    print(f"\nScope columns: {scope_cols}")
    if scope_cols:
        print(f"Unique scopes: {df[scope_cols[0]].dropna().unique().tolist()[:10]}")
    
    # Filter Electrical Equipment and check
    sector_name = "Electrical Equipment and Machinery"
    elec_df = df[df['sector'] == sector_name]
    print(f"\n=== {sector_name} ===")
    print(f"Total rows: {len(elec_df)}")
    scope_12 = elec_df[elec_df['scope'].astype(str).str.contains('1', na=False)]
    print(f"Scope 1 or 1+2 rows: {len(scope_12)}")
    print(f"Target values (first 10): {scope_12['target_value'].dropna().head(10).tolist()}")

if COMPANIES_FILE.exists():
    df = pd.read_excel(COMPANIES_FILE)
    print("\n\n=== COMPANIES FILE ===")
    print(f"Columns: {list(df.columns)}")
    print(f"Total rows: {len(df)}")

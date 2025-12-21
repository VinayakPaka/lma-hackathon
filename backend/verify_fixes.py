import sys
import os

# Add backend to path
sys.path.append("c:\\Users\\Vinayak Paka\\Desktop\\GreenGuard\\lma-hackathon\\backend")

try:
    print("Testing imports...")
    from app.services.ai_summary_service import ai_summary_service
    print("[OK] ai_summary_service imported")
    
    from app.services.sector_matching_service import sector_matching_service
    print("[OK] sector_matching_service imported")
    
    from app.services.banker_report_service import banker_report_service
    print("[OK] banker_report_service imported")
    
    print("\nAll services imported successfully. The code is ready to run.")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    sys.exit(1)

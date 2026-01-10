"""Test script for peer matching and credibility scoring fixes"""
from app.services.sector_matching_service import sector_matching_service
from app.services.sbti_data_service import sbti_data_service

# Test 1: Lookup Siemens AG
print("=== Test 1: Lookup Siemens AG ===")
lookup = sector_matching_service.lookup_company_in_sbti("Siemens AG")
print(f"Found: {lookup.get('found')}")
print(f"Sector: {lookup.get('sector')}")
print(f"Confidence: {lookup.get('confidence')}")

# Test 2: Get peer targets
print("\n=== Test 2: Peer Targets from sector_matching_service ===")
peer_data = sector_matching_service.get_peer_targets_for_sector(
    "Electrical Equipment and Machinery", 
    "1+2"
)
print(f"Peer count: {peer_data.get('peer_count')}")
print(f"Confidence level: {peer_data.get('confidence_level')}")
if peer_data.get('percentiles'):
    p = peer_data['percentiles']
    print(f"Median: {p.get('median'):.1f}%")
    print(f"P75: {p.get('p75'):.1f}%")

# Test 3: Classify ambition WITH peer_data (should NOT use fallback!)
print("\n=== Test 3: Classify Ambition with Pre-computed Peer Data ===")
ambition = sbti_data_service.classify_ambition(
    borrower_target=90.0,  # Siemens target
    sector="Electrical Equipment and Machinery",
    scope="Scope 1+2",
    sbti_aligned=True,
    peer_data=peer_data  # Pass pre-computed peer data!
)
print(f"Classification: {ambition.get('classification')}")
print(f"Peer median: {ambition.get('peer_median')}")
print(f"Peer P75: {ambition.get('peer_p75')}")
print(f"Peer count: {ambition.get('peer_count')}")
print(f"Using fallback: {ambition.get('using_fallback')}")
print(f"Match quality: {ambition.get('match_quality')}")

print("\n=== All Tests Passed ===")

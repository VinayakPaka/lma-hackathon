"""
GreenGuard ESG Platform - Configuration and Embedding Test Script
Run this to verify your API configuration and test embedding generation.
"""
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings

def check_config():
    """Check all required configuration values."""
    print("=" * 60)
    print("GreenGuard Configuration Check")
    print("=" * 60)
    
    issues = []
    
    # Check Voyage AI
    print("\n1. Voyage AI (Embeddings):")
    if settings.VOYAGE_API_KEY:
        masked_key = settings.VOYAGE_API_KEY[:8] + "..." + settings.VOYAGE_API_KEY[-4:]
        print(f"   [OK] VOYAGE_API_KEY: {masked_key}")
        print(f"   [OK] VOYAGE_EMBEDDING_MODEL: {settings.VOYAGE_EMBEDDING_MODEL}")
        print(f"   [OK] EMBEDDING_DIMENSION: {settings.EMBEDDING_DIMENSION}")
    else:
        print("   [FAIL] VOYAGE_API_KEY: NOT CONFIGURED")
        issues.append("VOYAGE_API_KEY is missing - embeddings will not work")
    
    # Check Supabase
    print("\n2. Supabase (Vector Storage):")
    if settings.SUPABASE_URL:
        print(f"   [OK] SUPABASE_URL: {settings.SUPABASE_URL}")
    else:
        print("   [FAIL] SUPABASE_URL: NOT CONFIGURED")
        issues.append("SUPABASE_URL is missing - vector storage will not work")
    
    if settings.SUPABASE_KEY:
        masked_key = settings.SUPABASE_KEY[:20] + "..."
        print(f"   [OK] SUPABASE_KEY: {masked_key}")
    else:
        print("   [FAIL] SUPABASE_KEY: NOT CONFIGURED")
        issues.append("SUPABASE_KEY is missing - vector storage will not work")
    
    # Check Perplexity AI
    print("\n3. Perplexity AI (LLM Analysis):")
    if settings.PERPLEXITY_API_KEY:
        masked_key = settings.PERPLEXITY_API_KEY[:8] + "..." + settings.PERPLEXITY_API_KEY[-4:]
        print(f"   [OK] PERPLEXITY_API_KEY: {masked_key}")
        print(f"   [OK] PERPLEXITY_MODEL: {settings.PERPLEXITY_MODEL}")
    else:
        print("   [FAIL] PERPLEXITY_API_KEY: NOT CONFIGURED")
        issues.append("PERPLEXITY_API_KEY is missing - AI analysis will use fallback")
    
    # Check Database
    print("\n4. Database:")
    print(f"   [OK] DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    
    # Summary
    print("\n" + "=" * 60)
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"   [!] {issue}")
        print("\nPlease update your .env file with the missing values.")
    else:
        print("[OK] All configuration looks good!")
    print("=" * 60)
    
    return len(issues) == 0


def test_voyage_embedding():
    """Test Voyage AI embedding generation."""
    print("\n" + "=" * 60)
    print("Testing Voyage AI Embedding Generation")
    print("=" * 60)
    
    if not settings.VOYAGE_API_KEY:
        print("[FAIL] Cannot test - VOYAGE_API_KEY is not configured")
        return False
    
    try:
        from app.services.embedding_service import embedding_service
        
        test_text = "This is a test document about carbon emissions and renewable energy. The company reduced emissions by 20%."
        
        print(f"\nTest text: '{test_text[:50]}...'")
        print("Generating embedding...")
        
        embedding = embedding_service.generate_embedding(test_text)
        
        print(f"[OK] Successfully generated embedding!")
        print(f"  Dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to generate embedding: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_supabase_connection():
    """Test Supabase connection."""
    print("\n" + "=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        print("[FAIL] Cannot test - Supabase is not configured")
        return False
    
    try:
        from supabase import create_client
        
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        # Try to query the document_embeddings table
        result = client.table("document_embeddings").select("id").limit(1).execute()
        
        print(f"[OK] Successfully connected to Supabase!")
        print(f"  document_embeddings table exists: YES")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to connect to Supabase: {type(e).__name__}: {str(e)}")
        if "relation" in str(e).lower() or "table" in str(e).lower():
            print("\n  TIP: You may need to run supabase_setup.sql in your Supabase SQL Editor")
        return False


def test_full_embedding_pipeline():
    """Test the full embedding pipeline with test text."""
    print("\n" + "=" * 60)
    print("Testing Full Embedding Pipeline")
    print("=" * 60)
    
    if not settings.VOYAGE_API_KEY or not settings.SUPABASE_URL:
        print("[FAIL] Cannot test - Voyage AI or Supabase is not configured")
        return False
    
    try:
        from app.services.embedding_service import embedding_service
        
        test_text = """
        GreenGuard ESG Report 2024
        
        This sustainability report outlines our commitment to environmental, social, and governance excellence.
        
        Carbon Emissions: We reduced our carbon footprint by 25% this year, achieving 1,500 tonnes CO2 equivalent.
        Energy Usage: Our facilities consumed 250,000 kWh of electricity, with 60% from renewable sources.
        Water Management: Water usage decreased to 50,000 cubic meters through efficiency improvements.
        Waste Recycling: We achieved a 75% waste recycling rate across all operations.
        
        Social Initiatives:
        - Employee diversity programs reaching 40% representation
        - Community investment of $2 million
        - Zero workplace incidents
        
        Governance:
        - Board independence at 80%
        - ESG committee established
        - TCFD-aligned reporting implemented
        """
        
        print("Test text length:", len(test_text), "characters")
        
        # Step 1: Chunk the text
        print("\n1. Chunking text...")
        chunks = embedding_service.chunk_text(test_text)
        print(f"   Created {len(chunks)} chunks")
        
        # Step 2: Generate embeddings
        print("\n2. Generating embeddings...")
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.generate_embeddings_batch(chunk_texts)
        print(f"   Generated {len(embeddings)} embeddings")
        
        # Step 3: Test storage (use a test document ID)
        print("\n3. Testing storage...")
        test_doc_id = 99999  # Use a test ID
        
        # First clean up any previous test
        try:
            embedding_service.delete_document_embeddings(test_doc_id)
        except:
            pass
        
        # Store embeddings
        embedding_ids = embedding_service.store_embeddings(test_doc_id, chunks, embeddings)
        print(f"   Stored {len(embedding_ids)} embeddings")
        
        # Step 4: Test retrieval
        print("\n4. Testing retrieval...")
        results = embedding_service.search_similar(
            query="carbon emissions reduction",
            document_id=test_doc_id,
            top_k=2
        )
        print(f"   Found {len(results)} similar chunks")
        if results:
            print(f"   Top result similarity: {results[0].get('similarity', 'N/A')}")
            print(f"   Top result content preview: {results[0].get('content', '')[:100]}...")
        
        # Clean up test data
        print("\n5. Cleaning up test data...")
        embedding_service.delete_document_embeddings(test_doc_id)
        print("   [OK] Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("[OK] Full embedding pipeline test PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Pipeline test FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GreenGuard ESG Platform - Embedding System Test")
    print("=" * 60)
    
    config_ok = check_config()
    
    if not config_ok:
        print("\n[!] Please fix configuration issues before running tests.")
        print("  Make sure your .env file has all required API keys.")
        sys.exit(1)
    
    # Run tests
    voyage_ok = test_voyage_embedding()
    supabase_ok = test_supabase_connection()
    
    if voyage_ok and supabase_ok:
        pipeline_ok = test_full_embedding_pipeline()
    else:
        print("\n[!] Skipping full pipeline test due to earlier failures.")
        pipeline_ok = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("Test Results Summary:")
    print(f"  Configuration: {'[OK] PASS' if config_ok else '[FAIL]'}")
    print(f"  Voyage AI:     {'[OK] PASS' if voyage_ok else '[FAIL]'}")
    print(f"  Supabase:      {'[OK] PASS' if supabase_ok else '[FAIL]'}")
    print(f"  Full Pipeline: {'[OK] PASS' if pipeline_ok else '[FAIL]'}")
    print("=" * 60)
    
    if voyage_ok and supabase_ok and pipeline_ok:
        print("\n[OK] All tests passed! Embedding system is ready.")
    else:
        print("\n[FAIL] Some tests failed. Please check the errors above.")


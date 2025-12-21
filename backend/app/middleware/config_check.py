"""
Middleware to check critical configuration on startup.
"""
import logging
from fastapi import FastAPI
from app.config import settings

logger = logging.getLogger(__name__)

def check_configuration():
    """Check critical configuration and log warnings."""
    issues = []
    warnings = []
    
    # Check AI API Keys
    if not settings.PERPLEXITY_API_KEY:
        issues.append("PERPLEXITY_API_KEY is not configured")
        logger.error("❌ PERPLEXITY_API_KEY is NOT configured!")
        logger.error("   AI analysis will fail. Please set it in your .env file.")
    else:
        logger.info(f"✅ PERPLEXITY_API_KEY configured (model: {settings.PERPLEXITY_MODEL})")
    
    if not settings.VOYAGE_API_KEY:
        issues.append("VOYAGE_API_KEY is not configured")
        logger.error("❌ VOYAGE_API_KEY is NOT configured!")
        logger.error("   Embeddings and RAG will not work. Please set it in your .env file.")
    else:
        logger.info(f"✅ VOYAGE_API_KEY configured (model: {settings.VOYAGE_EMBEDDING_MODEL})")
    
    # Check Supabase
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        issues.append("Supabase configuration incomplete")
        logger.error("❌ Supabase is NOT configured!")
        logger.error("   Vector storage will not work. Please set SUPABASE_URL and SUPABASE_KEY.")
    else:
        logger.info("✅ Supabase configured for vector storage")
    
    # Check database
    if "sqlite" in settings.DATABASE_URL.lower():
        warnings.append("Using SQLite database")
        logger.warning("⚠️  Using SQLite database (OK for development, use PostgreSQL for production)")
    else:
        logger.info("✅ Using PostgreSQL database")
    
    # Summary
    if issues:
        logger.error("=" * 80)
        logger.error("⚠️  CRITICAL CONFIGURATION ISSUES DETECTED:")
        for issue in issues:
            logger.error(f"   - {issue}")
        logger.error("=" * 80)
        logger.error("The application will run but core features will not work properly!")
        logger.error("Please check backend/.env.example and configure your .env file.")
        logger.error("=" * 80)
    else:
        logger.info("=" * 80)
        logger.info("✅ All critical configuration checks passed!")
        logger.info("=" * 80)
    
    if warnings:
        for warning in warnings:
            logger.warning(f"⚠️  {warning}")
    
    return len(issues) == 0

def add_config_check_middleware(app: FastAPI):
    """Add configuration check to FastAPI app startup."""
    @app.on_event("startup")
    async def startup_config_check():
        check_configuration()

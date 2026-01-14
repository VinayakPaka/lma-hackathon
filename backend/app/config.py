"""
GreenGuard ESG Platform - Configuration Settings
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application
    APP_NAME: str = "GreenGuard ESG Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database (use SQLite for local dev, PostgreSQL for production)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite+aiosqlite:///./greenguard.db"
    )
    
    # JWT Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = ["pdf", "png", "jpg", "jpeg", "tiff"]
    
    # OCR Settings
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    # ESG Scoring Weights
    CARBON_WEIGHT: float = 0.25
    ENERGY_WEIGHT: float = 0.25
    TAXONOMY_WEIGHT: float = 0.30
    WASTE_WEIGHT: float = 0.20
    
    # AI Configuration - Bytez (Primary)
    BYTEZ_API_KEY: str = os.getenv("BYTEZ_API_KEY", "")
    BYTEZ_MODEL_OPEN: str = "Qwen/Qwen3-4B-Instruct-2507"
    BYTEZ_MODEL_CLOSED: str = "openai/gpt-5"
    
    # Perplexity AI (Fallback)
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    PERPLEXITY_MODEL: str = os.getenv("PERPLEXITY_MODEL", "sonar")
    PERPLEXITY_API_URL: str = "https://api.perplexity.ai/chat/completions"
    
    # Voyage AI for Embeddings
    VOYAGE_API_KEY: str = os.getenv("VOYAGE_API_KEY", "")
    VOYAGE_EMBEDDING_MODEL: str = os.getenv("VOYAGE_EMBEDDING_MODEL", "voyage-3.5")
    EMBEDDING_DIMENSION: int = 1024
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # RAG Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    
    # OpenRouter (Secondary Fallback)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_KEY_2: str = os.getenv("OPENROUTER_API_KEY_2", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Ollama Configuration (Local)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Supermemory Configuration
    SUPERMEMORY_API_KEY: str = os.getenv("SUPERMEMORY_API_KEY", "")
    
    class Config:
        # Use absolute path to find .env file, regardless of where the app is run from
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

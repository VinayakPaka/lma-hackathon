"""
GreenGuard ESG Platform - Database Configuration
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from app.config import settings

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata


# Create async engine - SQLite doesn't support pool settings
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        connect_args={"check_same_thread": False}
    )
else:
    # For PostgreSQL with Supabase/PgBouncer, disable prepared statement caching
    # IMPORTANT: PgBouncer in transaction mode doesn't support prepared statements
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        pool_size=10,  # Increased from 2 to handle concurrent requests
        max_overflow=10,  # Increased from 3 for better concurrency
        pool_recycle=300,  # Increased to 5 minutes (less aggressive recycling)
        pool_timeout=30,
        connect_args={
            "statement_cache_size": 0,  # CRITICAL: Disable statement caching for PgBouncer
            "prepared_statement_cache_size": 0,  # CRITICAL: Disable prepared statement cache
            "command_timeout": 60,
            "server_settings": {
                "application_name": "greenguard_backend",
                "jit": "off"  # Disable JIT for better PgBouncer compatibility
            }
        }
    )

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session with retry logic."""
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
            return  # Success, exit the retry loop
        except Exception as e:
            # Check if it's a connection error
            error_msg = str(e).lower()
            is_connection_error = any(phrase in error_msg for phrase in [
                "connection", "timeout", "authentication", "refused", "reset"
            ])
            
            if is_connection_error and attempt < max_retries - 1:
                import logging
                import asyncio
                logger = logging.getLogger(__name__)
                logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                continue
            else:
                raise  # Re-raise if not a connection error or max retries exceeded


async def init_db():
    """Initialize database tables."""
    # For Supabase/PostgreSQL, tables are created manually via SQL Editor
    # Skip automatic creation to avoid PgBouncer prepared statement issues
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection."""
    await engine.dispose()

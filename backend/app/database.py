"""
GreenGuard ESG Platform - Database Configuration
"""
import logging
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

logger = logging.getLogger(__name__)


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # During error unwinding, the underlying connection may already be closed.
            # Rollback is best-effort; never mask the original exception.
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.warning("DB rollback failed during exception handling: %s", rollback_error)
            raise
        finally:
            # Close is also best-effort; don't raise during FastAPI dependency teardown.
            try:
                await session.close()
            except Exception as close_error:
                logger.warning("DB session close failed during teardown: %s", close_error)


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

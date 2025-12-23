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
        pool_size=2,  # Keep pool small for PgBouncer
        max_overflow=3,
        pool_recycle=60,  # Recycle connections every 60 seconds
        pool_timeout=30,
        connect_args={
            "statement_cache_size": 0,  # CRITICAL: Disable statement caching for PgBouncer
            "prepared_statement_cache_size": 0,  # CRITICAL: Disable prepared statement cache
            "command_timeout": 60,
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
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


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

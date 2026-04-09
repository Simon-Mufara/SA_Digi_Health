"""
Async database configuration with connection pooling for PostgreSQL.
Falls back to sync SQLite for local development.
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# Base for all models
Base = declarative_base()

# Determine database URL
DATABASE_URL = settings.database_url
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

# Async engine for PostgreSQL
if IS_POSTGRES:
    # Convert to async URL
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=settings.debug if hasattr(settings, 'debug') else False,
    )
    
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # Sync engine for migrations and compatibility
    sync_engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    
    SyncSessionLocal = sessionmaker(
        bind=sync_engine,
        autocommit=False,
        autoflush=False,
    )
    
    USE_ASYNC = True
    
else:
    # SQLite fallback (sync only)
    from pathlib import Path
    sqlite_path = Path(__file__).resolve().parents[2] / "clinic_local.db"
    SQLITE_URL = f"sqlite:///{sqlite_path}"
    
    sync_engine = create_engine(
        SQLITE_URL,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )
    
    SyncSessionLocal = sessionmaker(
        bind=sync_engine,
        autocommit=False,
        autoflush=False,
    )
    
    # No async for SQLite in this setup
    async_engine = None
    AsyncSessionLocal = None
    USE_ASYNC = False
    
    print(f"⚠️  Using SQLite fallback at {sqlite_path}")


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Async database session dependency for FastAPI."""
    if not USE_ASYNC or AsyncSessionLocal is None:
        raise RuntimeError("Async database not available. Use get_sync_db() instead.")
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Sync database session dependency for FastAPI."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    """
    Universal database dependency.
    Returns sync session (works with both PostgreSQL and SQLite).
    """
    return get_sync_db()


async def init_db():
    """Initialize database tables."""
    if USE_ASYNC and async_engine:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        Base.metadata.create_all(bind=sync_engine)


def init_db_sync():
    """Synchronously initialize database tables."""
    Base.metadata.create_all(bind=sync_engine)

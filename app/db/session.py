"""
Async SQLAlchemy session/engine configuration.

This module provides the async engine and async session factory used throughout the app.
"""

from __future__ import annotations

from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings

_engine: Optional[AsyncEngine] = None
_sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None


def _build_engine(database_url: str) -> AsyncEngine:
    """
    Build an AsyncEngine from a DSN.

    Notes:
        - DATABASE_URL should be an async driver URL for Postgres, e.g.:
          postgresql+asyncpg://user:password@host:5432/dbname
    """
    return create_async_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )


# PUBLIC_INTERFACE
def get_engine(*, settings: Optional[Settings] = None) -> AsyncEngine:
    """
    PUBLIC_INTERFACE
    Return a lazily-initialized global AsyncEngine.

    Args:
        settings: Optional Settings override (useful for tests). If omitted, loads from env.

    Returns:
        A singleton AsyncEngine instance.
    """
    global _engine  # noqa: PLW0603

    if _engine is not None:
        return _engine

    resolved_settings = settings or get_settings()
    if not resolved_settings.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not configured. Set DATABASE_URL in the environment/.env "
            "(e.g. postgresql+asyncpg://user:pass@host:5432/dbname)."
        )

    _engine = _build_engine(resolved_settings.DATABASE_URL)
    return _engine


# PUBLIC_INTERFACE
def get_sessionmaker(*, settings: Optional[Settings] = None) -> async_sessionmaker[AsyncSession]:
    """
    PUBLIC_INTERFACE
    Return a lazily-initialized global async_sessionmaker.

    Args:
        settings: Optional Settings override (useful for tests). If omitted, loads from env.

    Returns:
        An async_sessionmaker configured for AsyncSession.
    """
    global _sessionmaker  # noqa: PLW0603

    if _sessionmaker is not None:
        return _sessionmaker

    engine = get_engine(settings=settings)
    _sessionmaker = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
        autoflush=False,
        autocommit=False,
    )
    return _sessionmaker


# PUBLIC_INTERFACE
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """
    PUBLIC_INTERFACE
    FastAPI dependency that yields an AsyncSession.

    Usage:
        from fastapi import Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.dependencies.db import get_db_session

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db_session)):
            ...

    Yields:
        An AsyncSession, closed after the request finishes.
    """
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session

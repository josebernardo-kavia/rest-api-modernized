"""Database dependency providers for FastAPI."""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    PUBLIC_INTERFACE
    FastAPI dependency that yields an AsyncSession.

    Returns:
        An async generator yielding an AsyncSession.
    """
    async for session in get_async_session():
        yield session

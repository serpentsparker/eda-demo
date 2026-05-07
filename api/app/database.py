"""Async SQLAlchemy engine and session factory for the API."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_engine = create_async_engine(settings.database_url, pool_pre_ping=True)
_async_session = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Yield an async database session for use as a FastAPI dependency."""
    async with _async_session() as session:
        yield session

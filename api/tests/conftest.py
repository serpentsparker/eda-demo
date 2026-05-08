"""Fixtures for API unit tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def mock_db_session() -> AsyncMock:
    """Return a mock async database session."""
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
async def api_client(mock_db_session: AsyncMock) -> AsyncGenerator[AsyncClient]:
    """Return an async test client with the database dependency overridden."""
    from app.database import get_session
    from app.main import app

    async def override_get_session() -> AsyncGenerator[AsyncMock]:
        yield mock_db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

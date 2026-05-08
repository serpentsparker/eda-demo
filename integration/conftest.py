"""Integration test fixtures — require the full Docker Compose stack to be running."""

import os

import httpx
import pytest

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: marks tests that require the full stack to be running",
    )


@pytest.fixture(scope="session")
def api_client() -> httpx.Client:
    """Return an HTTP client pointed at the running API."""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client

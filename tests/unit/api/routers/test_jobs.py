"""Unit tests for the jobs router endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture(autouse=True)
def clear_jobs_store() -> None:
    """Reset the in-memory jobs store before each test to prevent state leakage."""
    from app.routers.jobs import _jobs

    _jobs.clear()
    yield
    _jobs.clear()


async def test_submit_job_returns_202_with_pending_status(
    api_client: AsyncClient,
) -> None:
    """POST /jobs should return HTTP 202 with the generated job_id and pending status."""
    fake_id = "01J8ABCDEF000000000000000"
    with patch(
        "app.routers.jobs.publish_job_requested",
        new_callable=AsyncMock,
        return_value=fake_id,
    ):
        response = await api_client.post(
            "/jobs",
            json={"job_type": "echo", "parameters": {"message": "hello"}},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == fake_id
    assert body["status"] == "pending"


async def test_get_job_returns_current_status(api_client: AsyncClient) -> None:
    """GET /jobs/{job_id} should return the status recorded at submission time."""
    fake_id = "01J8ABCDEF000000000000001"
    with patch(
        "app.routers.jobs.publish_job_requested",
        new_callable=AsyncMock,
        return_value=fake_id,
    ):
        await api_client.post("/jobs", json={"job_type": "echo"})

    response = await api_client.get(f"/jobs/{fake_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == fake_id
    assert body["status"] == "pending"


async def test_get_job_returns_404_for_unknown_id(api_client: AsyncClient) -> None:
    """GET /jobs/{job_id} should return 404 when the job_id does not exist."""
    response = await api_client.get("/jobs/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


async def test_submit_job_stores_pending_status(api_client: AsyncClient) -> None:
    """Submitting a job should create an entry in the jobs store with pending status."""
    fake_id = "01J8ABCDEF000000000000002"
    with patch(
        "app.routers.jobs.publish_job_requested",
        new_callable=AsyncMock,
        return_value=fake_id,
    ):
        await api_client.post("/jobs", json={"job_type": "echo"})

    from app.routers.jobs import _jobs
    from app.schemas.jobs import JobStatus

    assert _jobs[fake_id] == JobStatus.PENDING

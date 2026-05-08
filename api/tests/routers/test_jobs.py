"""Unit tests for the jobs router endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient

from app.models.jobs import Job
from app.schemas.jobs import JobStatus

_FAKE_JOB_ID = uuid.UUID("018e4e1a-0000-7000-8000-000000000001")


async def test_submit_job_returns_202_with_pending_status(
    api_client: AsyncClient,
) -> None:
    """POST /jobs should return HTTP 202 with the generated job_id and pending status."""
    with (
        patch("app.routers.jobs.uuid.uuid7", return_value=_FAKE_JOB_ID),
        patch("app.routers.jobs.publish_job_requested", new_callable=AsyncMock),
    ):
        response = await api_client.post(
            "/jobs",
            json={"job_type": "echo", "parameters": {"message": "hello"}},
        )

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"] == str(_FAKE_JOB_ID)
    assert body["status"] == "pending"


async def test_get_job_returns_current_status(
    api_client: AsyncClient,
    mock_db_session: AsyncMock,
) -> None:
    """GET /jobs/{job_id} should return the status for a known job_id."""
    mock_db_session.get = AsyncMock(
        return_value=Job(id=_FAKE_JOB_ID, job_type="echo", parameters={}, status=JobStatus.PENDING)
    )

    response = await api_client.get(f"/jobs/{_FAKE_JOB_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == str(_FAKE_JOB_ID)
    assert body["status"] == "pending"


async def test_get_job_returns_404_for_unknown_id(
    api_client: AsyncClient,
    mock_db_session: AsyncMock,
) -> None:
    """GET /jobs/{job_id} should return 404 when the job_id does not exist."""
    mock_db_session.get = AsyncMock(return_value=None)
    unknown_id = uuid.UUID("018e4e1a-0000-7000-8000-000000000000")

    response = await api_client.get(f"/jobs/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


async def test_submit_job_persists_pending_status(
    api_client: AsyncClient,
    mock_db_session: AsyncMock,
) -> None:
    """POST /jobs should persist a new Job record with pending status before publishing."""
    with (
        patch("app.routers.jobs.uuid.uuid7", return_value=_FAKE_JOB_ID),
        patch("app.routers.jobs.publish_job_requested", new_callable=AsyncMock),
    ):
        await api_client.post("/jobs", json={"job_type": "echo"})

    mock_db_session.add.assert_called_once()
    job_arg = mock_db_session.add.call_args[0][0]
    assert job_arg.id == _FAKE_JOB_ID
    assert job_arg.status == JobStatus.PENDING
    # commit must be called before publish_job_requested to avoid race conditions
    mock_db_session.commit.assert_called_once()

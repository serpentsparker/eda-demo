"""End-to-end integration tests for the full API + Worker stack.

Requires the complete Docker Compose stack to be running:
    docker compose -f docker/docker-compose.yml up --build
"""

import time

import httpx
import pytest


def _poll_status(client: httpx.Client, job_id: str, timeout: float = 15.0) -> str:
    """Poll GET /jobs/{job_id} until the status is terminal or the timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        status = response.json()["status"]
        if status in ("completed", "failed"):
            return status
        time.sleep(0.5)
    raise TimeoutError(
        f"Job {job_id} did not reach a terminal status within {timeout}s"
    )


@pytest.mark.integration
def test_echo_job_completes_end_to_end(api_client: httpx.Client) -> None:
    """Submitting an echo job should transition from pending to completed."""
    response = api_client.post(
        "/jobs",
        json={"job_type": "echo", "parameters": {"message": "hello"}},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    job_id = body["job_id"]

    final_status = _poll_status(api_client, job_id)
    assert final_status == "completed"


@pytest.mark.integration
def test_unknown_job_type_fails_end_to_end(api_client: httpx.Client) -> None:
    """Submitting a job with an unknown type should transition to failed."""
    response = api_client.post(
        "/jobs",
        json={"job_type": "nonexistent", "parameters": {}},
    )
    assert response.status_code == 202
    job_id = response.json()["job_id"]

    final_status = _poll_status(api_client, job_id)
    assert final_status == "failed"

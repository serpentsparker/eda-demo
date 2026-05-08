"""Unit tests for the API EventBridge event publisher."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.events.publisher import publish_job_requested
from app.schemas.jobs import JobRequest


@pytest.fixture(autouse=True)
def clear_client_cache() -> None:
    """Clear the cached boto3 client between tests."""
    from app.events import publisher

    publisher._get_events_client.cache_clear()
    yield
    publisher._get_events_client.cache_clear()


async def test_publish_job_requested_calls_put_events_with_correct_fields() -> None:
    """publish_job_requested should PUT a JobRequested event with the right source and detail."""
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 0,
        "Entries": [{"EventId": "abc"}],
    }

    with patch("app.events.publisher._get_events_client", return_value=mock_client):
        await publish_job_requested(
            job_id="01J8ABCDEF000000000000001",
            payload=JobRequest(job_type="echo", parameters={"k": "v"}),
        )

    mock_client.put_events.assert_called_once()
    entries = mock_client.put_events.call_args.kwargs["Entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["Source"] == "eda-demo.api"
    assert entry["DetailType"] == "JobRequested"
    detail = json.loads(entry["Detail"])
    assert detail["job_id"] == "01J8ABCDEF000000000000001"
    assert detail["job_type"] == "echo"
    assert detail["parameters"] == {"k": "v"}


async def test_publish_job_requested_raises_on_eventbridge_failure() -> None:
    """publish_job_requested should raise RuntimeError when EventBridge rejects the entry."""
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 1,
        "Entries": [{"ErrorCode": "err"}],
    }

    with (
        patch("app.events.publisher._get_events_client", return_value=mock_client),
        pytest.raises(RuntimeError, match="Failed to publish JobRequested event"),
    ):
        await publish_job_requested(
            job_id="01J8ABCDEF000000000000001",
            payload=JobRequest(job_type="echo"),
        )

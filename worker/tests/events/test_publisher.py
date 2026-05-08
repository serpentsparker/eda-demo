"""Unit tests for the worker EventBridge event publisher."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.events.publisher import publish_job_completed, publish_job_failed


@pytest.fixture(autouse=True)
def clear_client_cache() -> None:
    """Clear the cached boto3 client between tests."""
    from app.events import publisher

    publisher._get_events_client.cache_clear()
    yield
    publisher._get_events_client.cache_clear()


def test_publish_job_completed_calls_put_events_with_correct_fields() -> None:
    """publish_job_completed should PUT a JobCompleted event with job_id and result."""
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 0,
        "Entries": [{"EventId": "abc"}],
    }

    with patch("app.events.publisher._get_events_client", return_value=mock_client):
        publish_job_completed(job_id="job-1", result={"echo": {"k": "v"}})

    mock_client.put_events.assert_called_once()
    entries = mock_client.put_events.call_args.kwargs["Entries"]
    entry = entries[0]
    assert entry["Source"] == "eda-demo.worker"
    assert entry["DetailType"] == "JobCompleted"
    detail = json.loads(entry["Detail"])
    assert detail["job_id"] == "job-1"
    assert detail["result"] == {"echo": {"k": "v"}}
    assert "completed_at" in detail


def test_publish_job_failed_calls_put_events_with_correct_fields() -> None:
    """publish_job_failed should PUT a JobFailed event with job_id and error."""
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 0,
        "Entries": [{"EventId": "abc"}],
    }

    with patch("app.events.publisher._get_events_client", return_value=mock_client):
        publish_job_failed(job_id="job-2", error="something went wrong")

    entries = mock_client.put_events.call_args.kwargs["Entries"]
    entry = entries[0]
    assert entry["DetailType"] == "JobFailed"
    detail = json.loads(entry["Detail"])
    assert detail["job_id"] == "job-2"
    assert detail["error"] == "something went wrong"
    assert "failed_at" in detail


def test_publish_job_completed_raises_on_eventbridge_failure() -> None:
    """publish_job_completed should raise RuntimeError when EventBridge rejects the entry."""
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 1,
        "Entries": [{"ErrorCode": "err"}],
    }

    with (
        patch("app.events.publisher._get_events_client", return_value=mock_client),
        pytest.raises(RuntimeError, match="Failed to publish JobCompleted event"),
    ):
        publish_job_completed(job_id="job-3", result={})


def test_publish_job_failed_raises_on_eventbridge_failure() -> None:
    """publish_job_failed should raise RuntimeError when EventBridge rejects the entry."""
    mock_client = MagicMock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 1,
        "Entries": [{"ErrorCode": "err"}],
    }

    with (
        patch("app.events.publisher._get_events_client", return_value=mock_client),
        pytest.raises(RuntimeError, match="Failed to publish JobFailed event"),
    ):
        publish_job_failed(job_id="job-4", error="boom")

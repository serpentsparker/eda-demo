"""Unit tests for the SQS event consumer."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.events.consumer import _handle_message


@pytest.fixture(autouse=True)
def clear_sqs_client_cache() -> None:
    """Clear the cached SQS boto3 client between tests."""
    from app.events import consumer

    consumer._get_sqs_client.cache_clear()
    yield
    consumer._get_sqs_client.cache_clear()


def _make_message(body: dict) -> dict:
    return {"Body": json.dumps(body), "MessageId": "test-msg-id", "ReceiptHandle": "rh"}


def test_handle_message_dispatches_handle_job_for_job_requested() -> None:
    """A JobRequested event should invoke handle_job with the correct arguments."""
    message = _make_message(
        {
            "detail-type": "JobRequested",
            "detail": {
                "job_id": "job-123",
                "job_type": "echo",
                "parameters": {"msg": "hello"},
            },
        }
    )

    mock_handle = MagicMock()
    with patch("app.handlers.job_handler.handle_job", mock_handle):
        _handle_message(message)

    mock_handle.assert_called_once_with(
        job_id="job-123", job_type="echo", parameters={"msg": "hello"}
    )


def test_handle_message_ignores_unknown_event_type(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An event with an unrecognised detail-type should be skipped without dispatching."""
    message = _make_message({"detail-type": "SomethingElse", "detail": {}})

    with patch("app.handlers.job_handler.handle_job") as mock_handle:
        _handle_message(message)

    mock_handle.assert_not_called()


def test_handle_message_uses_detail_type_key_fallback() -> None:
    """DetailType (PascalCase) should be accepted as well as detail-type (kebab-case)."""
    message = _make_message(
        {
            "DetailType": "JobRequested",
            "detail": {"job_id": "job-456", "job_type": "echo", "parameters": {}},
        }
    )

    mock_handle = MagicMock()
    with patch("app.handlers.job_handler.handle_job", mock_handle):
        _handle_message(message)

    mock_handle.assert_called_once_with(job_id="job-456", job_type="echo", parameters={})

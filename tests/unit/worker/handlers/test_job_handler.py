"""Unit tests for the plain job handler."""

from unittest.mock import patch

import pytest

from app.handlers.job_handler import _dispatch, handle_job
from app.models.jobs import JobStatus


def test_dispatch_echo_returns_parameters() -> None:
    """Echo handler should return parameters unchanged."""
    params = {"message": "hello"}
    result = _dispatch("echo", params)
    assert result == {"echo": params}


def test_dispatch_unknown_job_type_raises_value_error() -> None:
    """Unknown job_type should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown job_type"):
        _dispatch("nonexistent", {})


def test_handle_job_success_updates_status_and_publishes_completed() -> None:
    """handle_job should mark the job running then completed, and publish JobCompleted."""
    params = {"msg": "hello"}

    with (
        patch("app.handlers.job_handler.update_job_status") as mock_update,
        patch("app.handlers.job_handler.publish_job_completed") as mock_completed,
    ):
        result = handle_job("job-1", "echo", params)

    assert result == {"echo": params}
    mock_completed.assert_called_once_with(job_id="job-1", result={"echo": params})
    mock_update.assert_any_call("job-1", JobStatus.RUNNING)
    mock_update.assert_any_call("job-1", JobStatus.COMPLETED)


def test_handle_job_failure_updates_status_and_publishes_failed() -> None:
    """handle_job should mark the job failed, publish JobFailed, and re-raise the exception."""
    error = ValueError("bad input")

    with (
        patch("app.handlers.job_handler._dispatch", side_effect=error),
        patch("app.handlers.job_handler.update_job_status") as mock_update,
        patch("app.handlers.job_handler.publish_job_failed") as mock_failed,
    ):
        with pytest.raises(ValueError, match="bad input"):
            handle_job("job-2", "echo", {})

    mock_failed.assert_called_once_with(job_id="job-2", error="bad input")
    mock_update.assert_any_call("job-2", JobStatus.RUNNING)
    mock_update.assert_any_call("job-2", JobStatus.FAILED)

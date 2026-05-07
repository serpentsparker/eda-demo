"""Unit tests for Celery job task dispatch logic."""

from unittest.mock import patch

import pytest
from celery.exceptions import Retry

from app.models.jobs import JobStatus
from app.tasks.job_tasks import _dispatch, process_job


def test_dispatch_echo_returns_parameters() -> None:
    """Echo handler should return parameters unchanged."""
    params = {"message": "hello"}
    result = _dispatch("echo", params)
    assert result == {"echo": params}


def test_dispatch_unknown_job_type_raises_value_error() -> None:
    """Unknown job_type should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown job_type"):
        _dispatch("nonexistent", {})


def test_process_job_success_updates_status_and_publishes_completed() -> None:
    """process_job should mark the job running then completed, and publish JobCompleted."""
    params = {"msg": "hello"}

    with (
        patch("app.tasks.job_tasks.update_job_status") as mock_update,
        patch("app.tasks.job_tasks.publish_job_completed") as mock_completed,
    ):
        eager_result = process_job.apply(args=["job-1", "echo", params])

    assert eager_result.get() == {"echo": params}
    mock_completed.assert_called_once_with(job_id="job-1", result={"echo": params})
    mock_update.assert_any_call("job-1", JobStatus.RUNNING)
    mock_update.assert_any_call("job-1", JobStatus.COMPLETED)


def test_process_job_failure_updates_status_and_publishes_failed() -> None:
    """process_job should mark the job failed, publish JobFailed, and raise Retry on error."""
    error = ValueError("bad input")

    with (
        patch.object(process_job, "retry", side_effect=Retry()),
        patch("app.tasks.job_tasks._dispatch", side_effect=error),
        patch("app.tasks.job_tasks.update_job_status") as mock_update,
        patch("app.tasks.job_tasks.publish_job_failed") as mock_failed,
    ):
        with pytest.raises(Retry):
            process_job.apply(args=["job-2", "echo", {}], throw=True)

    mock_failed.assert_called_once_with(job_id="job-2", error="bad input")
    mock_update.assert_any_call("job-2", JobStatus.RUNNING)
    mock_update.assert_any_call("job-2", JobStatus.FAILED)

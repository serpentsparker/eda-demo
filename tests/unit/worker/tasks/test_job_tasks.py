"""Unit tests for Celery job task dispatch logic."""

import pytest

from app.tasks.job_tasks import _dispatch


def test_dispatch_echo_returns_parameters() -> None:
    """Echo handler should return parameters unchanged."""
    params = {"message": "hello"}
    result = _dispatch("echo", params)
    assert result == {"echo": params}


def test_dispatch_unknown_job_type_raises_value_error() -> None:
    """Unknown job_type should raise ValueError."""
    with pytest.raises(ValueError, match="Unknown job_type"):
        _dispatch("nonexistent", {})

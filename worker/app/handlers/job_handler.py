"""Plain job handler — processes jobs dispatched from the SQS consumer."""

import logging
from typing import Any

from app.database import update_job_status
from app.events.publisher import publish_job_completed, publish_job_failed
from app.models.jobs import JobStatus

logger = logging.getLogger(__name__)


def handle_job(job_id: str, job_type: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Process a job received from the SQS consumer.

    Marks the job as running, dispatches it to the appropriate handler, then
    marks it completed or failed and publishes the outcome event.

    Args:
        job_id: Unique job identifier.
        job_type: Logical job type (routes to the correct handler).
        parameters: Arbitrary job parameters.

    Returns:
        A dict containing the job result.

    Raises:
        Exception: Re-raises any exception from the handler so the SQS consumer
            can leave the message in the queue for visibility-timeout retry.
    """
    logger.info("Starting job job_id=%s job_type=%s", job_id, job_type)
    update_job_status(job_id, JobStatus.RUNNING)
    try:
        result = _dispatch(job_type, parameters)
        update_job_status(job_id, JobStatus.COMPLETED)
        publish_job_completed(job_id=job_id, result=result)
        logger.info("Completed job job_id=%s", job_id)
        return result
    except Exception as exc:
        logger.exception("Job failed job_id=%s", job_id)
        update_job_status(job_id, JobStatus.FAILED)
        publish_job_failed(job_id=job_id, error=str(exc))
        raise


def _dispatch(job_type: str, parameters: dict[str, Any]) -> dict[str, Any]:
    """Route a job to its handler based on job_type.

    Args:
        job_type: Identifies which handler to invoke.
        parameters: Job-specific parameters.

    Returns:
        Handler result dict.

    Raises:
        ValueError: If job_type is unknown.
    """
    handlers = {
        "echo": _handle_echo,
    }
    handler = handlers.get(job_type)
    if handler is None:
        raise ValueError(f"Unknown job_type: {job_type!r}")
    return handler(parameters)


def _handle_echo(parameters: dict[str, Any]) -> dict[str, Any]:
    """Echo handler — returns parameters unchanged (useful for smoke testing)."""
    return {"echo": parameters}

"""Celery task definitions for job processing."""

import logging

from celery import Task

from app.events.publisher import publish_job_completed, publish_job_failed
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_job(self: Task, job_id: str, job_type: str, parameters: dict) -> dict:
    """Process a job dispatched from the API via EventBridge → SQS.

    Args:
        job_id: Unique job identifier.
        job_type: Logical job type (routes to the correct handler).
        parameters: Arbitrary job parameters.

    Returns:
        A dict containing the job result.
    """
    logger.info("Starting job job_id=%s job_type=%s", job_id, job_type)
    try:
        result = _dispatch(job_type, parameters)
        publish_job_completed(job_id=job_id, result=result)
        logger.info("Completed job job_id=%s", job_id)
        return result
    except Exception as exc:
        logger.exception("Job failed job_id=%s: %s", job_id, exc)
        publish_job_failed(job_id=job_id, error=str(exc))
        raise self.retry(exc=exc) from exc


def _dispatch(job_type: str, parameters: dict) -> dict:
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


def _handle_echo(parameters: dict) -> dict:
    """Echo handler — returns parameters unchanged (useful for smoke testing)."""
    return {"echo": parameters}

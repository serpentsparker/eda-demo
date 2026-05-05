"""EventBridge event publisher for the worker service."""

import functools
import json
import logging
from datetime import UTC, datetime
from typing import Any

import boto3
import botocore.client

from app.config import settings

logger = logging.getLogger(__name__)


@functools.cache
def _get_events_client(region: str, endpoint_url: str | None) -> botocore.client.BaseClient:
    """Return a cached boto3 EventBridge client."""
    kwargs: dict[str, str] = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("events", **kwargs)


def publish_job_completed(job_id: str, result: dict) -> None:
    """Publish a JobCompleted event to EventBridge.

    Args:
        job_id: The job that completed.
        result: The job result payload.
    """
    _put_event(
        detail_type="JobCompleted",
        detail={"job_id": job_id, "result": result, "completed_at": _now()},
    )
    logger.info("Published JobCompleted event job_id=%s", job_id)


def publish_job_failed(job_id: str, error: str) -> None:
    """Publish a JobFailed event to EventBridge.

    Args:
        job_id: The job that failed.
        error: Human-readable error description.
    """
    _put_event(
        detail_type="JobFailed",
        detail={"job_id": job_id, "error": error, "failed_at": _now()},
    )
    logger.warning("Published JobFailed event job_id=%s error=%s", job_id, error)


def _put_event(detail_type: str, detail: dict[str, Any]) -> None:
    client = _get_events_client(settings.aws_default_region, settings.localstack_endpoint)
    response = client.put_events(
        Entries=[
            {
                "Source": "eda-demo.worker",
                "DetailType": detail_type,
                "Detail": json.dumps(detail),
                "EventBusName": settings.eventbridge_bus_name,
            }
        ]
    )
    if response.get("FailedEntryCount", 0):
        logger.error("EventBridge put_events failed detail_type=%s: %s", detail_type, response)
        raise RuntimeError(f"Failed to publish {detail_type} event to EventBridge")


def _now() -> str:
    return datetime.now(UTC).isoformat()

"""EventBridge event publisher for the API service."""

import asyncio
import functools
import json
import logging
from datetime import UTC, datetime

import boto3
import botocore.client
from ulid import ULID

from app.config import settings
from app.schemas.jobs import JobRequest

logger = logging.getLogger(__name__)


@functools.cache
def _get_events_client(region: str, endpoint_url: str | None) -> botocore.client.BaseClient:
    """Return a cached boto3 EventBridge client."""
    kwargs: dict[str, str] = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("events", **kwargs)


async def publish_job_requested(payload: JobRequest) -> str:
    """Publish a JobRequested event to EventBridge and return the generated job ID.

    Args:
        payload: The incoming job request payload.

    Returns:
        The generated job ID (ULID string).
    """
    job_id = str(ULID())
    event_detail = {
        "job_id": job_id,
        "job_type": payload.job_type,
        "parameters": payload.parameters,
        "requested_at": datetime.now(UTC).isoformat(),
    }

    client = _get_events_client(settings.aws_default_region, settings.localstack_endpoint)
    response = await asyncio.to_thread(
        client.put_events,
        Entries=[
            {
                "Source": "eda-demo.api",
                "DetailType": "JobRequested",
                "Detail": json.dumps(event_detail),
                "EventBusName": settings.eventbridge_bus_name,
            }
        ],
    )

    failed = response.get("FailedEntryCount", 0)
    if failed:
        logger.error("EventBridge put_events failed for job_id=%s: %s", job_id, response)
        raise RuntimeError(f"Failed to publish JobRequested event for job {job_id}")

    logger.info("Published JobRequested event job_id=%s", job_id)
    return job_id

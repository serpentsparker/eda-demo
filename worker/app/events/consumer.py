"""SQS event consumer — polls demo-queue and dispatches jobs to handlers."""

import functools
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import boto3
import botocore.client

from app.config import settings

logger = logging.getLogger(__name__)

_WORKER_THREADS = 4


@functools.cache
def _get_sqs_client(region: str, endpoint_url: str | None) -> botocore.client.BaseClient:
    """Return a cached boto3 SQS client."""
    kwargs: dict[str, str] = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("sqs", **kwargs)


def _handle_message(message: dict[str, Any]) -> None:
    """Parse an EventBridge envelope from an SQS message and invoke the job handler.

    Args:
        message: Raw SQS message dict as returned by boto3 receive_message.

    Raises:
        KeyError: If a required field is missing from the event detail.
    """
    body = json.loads(message["Body"])
    detail_type = body.get("detail-type") or body.get("DetailType")

    if detail_type != "JobRequested":
        logger.warning("Ignoring unexpected event type: %s", detail_type)
        return

    detail = body["detail"]
    job_id: str = detail["job_id"]
    job_type: str = detail["job_type"]
    parameters: dict[str, Any] = detail.get("parameters", {})

    logger.info("Dispatching handle_job job_id=%s job_type=%s", job_id, job_type)

    from app.handlers.job_handler import handle_job

    handle_job(job_id=job_id, job_type=job_type, parameters=parameters)


def _process_message(sqs_client: botocore.client.BaseClient, message: dict[str, Any]) -> None:
    """Handle a single SQS message and delete it on success.

    Leaves the message in the queue on failure so SQS visibility timeout
    returns it for retry.

    Args:
        sqs_client: Boto3 SQS client used to delete the message.
        message: Raw SQS message dict as returned by boto3 receive_message.
    """
    receipt_handle = message["ReceiptHandle"]
    try:
        _handle_message(message)
        sqs_client.delete_message(
            QueueUrl=settings.sqs_queue_url,
            ReceiptHandle=receipt_handle,
        )
    except Exception:
        logger.exception(
            "Failed to handle SQS message %s — will not delete, "
            "visibility timeout will return it to the queue",
            message.get("MessageId"),
        )


def consume() -> None:
    """Long-poll demo-queue and dispatch each message to a thread-pool worker.

    Blocks indefinitely; intended to be called from the process entry point.
    """
    sqs_client = _get_sqs_client(settings.aws_default_region, settings.localstack_endpoint)
    logger.info("SQS consumer started, polling: %s", settings.sqs_queue_url)

    with ThreadPoolExecutor(max_workers=_WORKER_THREADS, thread_name_prefix="job-worker") as pool:
        while True:
            try:
                response = sqs_client.receive_message(
                    QueueUrl=settings.sqs_queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                )
                for message in response.get("Messages", []):
                    pool.submit(_process_message, sqs_client, message)
            except Exception:
                logger.exception("SQS polling error; retrying")

"""SQS event consumer — bridges EventBridge messages to Celery tasks."""

import functools
import json
import logging
import threading
from typing import Any

import boto3
import botocore.client
from celery.signals import worker_ready

from app.config import settings

logger = logging.getLogger(__name__)


@functools.cache
def _get_sqs_client(region: str, endpoint_url: str | None) -> botocore.client.BaseClient:
    """Return a cached boto3 SQS client."""
    kwargs: dict[str, str] = {"region_name": region}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("sqs", **kwargs)


def _handle_message(message: dict[str, Any]) -> None:
    """Parse an EventBridge envelope from an SQS message and dispatch the Celery task.

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

    logger.info("Dispatching process_job job_id=%s job_type=%s", job_id, job_type)

    # Late import to avoid a circular dependency: consumer <- worker <- job_tasks <- worker.
    from app.tasks.job_tasks import process_job

    process_job.apply_async(args=[job_id, job_type, parameters])


def _consumer_loop() -> None:
    """Long-poll demo-queue indefinitely, dispatching tasks for each JobRequested event."""
    sqs_client = _get_sqs_client(settings.aws_default_region, settings.localstack_endpoint)
    logger.info("SQS consumer started, polling: %s", settings.sqs_queue_url)

    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=settings.sqs_queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )
            for message in response.get("Messages", []):
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
        except Exception:
            logger.exception("SQS polling error; retrying")


@worker_ready.connect
def start_sqs_consumer(sender: object, **kwargs: object) -> None:
    """Start the SQS polling loop in a daemon thread when the Celery worker is ready.

    Args:
        sender: The Celery worker instance (unused).
        **kwargs: Additional signal keyword arguments (unused).
    """
    thread = threading.Thread(target=_consumer_loop, daemon=True, name="sqs-consumer")
    thread.start()
    logger.info("SQS consumer thread started")

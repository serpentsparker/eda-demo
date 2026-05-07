"""Celery application factory."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "eda-demo-worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.job_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Register the SQS event consumer so it starts with the worker process.
import app.events.consumer  # noqa: E402, F401

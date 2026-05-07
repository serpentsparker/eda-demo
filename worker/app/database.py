"""Synchronous SQLAlchemy engine and session factory for the worker."""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

_engine = create_engine(settings.database_sync_url, pool_pre_ping=True)
_session_factory = sessionmaker(_engine, expire_on_commit=False)


@contextmanager
def get_session() -> Generator[Session]:
    """Yield a synchronous database session."""
    with _session_factory() as session:
        yield session


def update_job_status(job_id: str, status: str) -> None:
    """Update the status of a job record in the database.

    Args:
        job_id: The unique job identifier.
        status: The new status value (e.g. "running", "completed", "failed").
    """
    from app.models.jobs import Job

    with get_session() as session:
        job = session.get(Job, job_id)
        if job is None:
            logger.warning("update_job_status: job_id=%s not found in database", job_id)
            return
        job.status = status
        session.commit()

"""SQLAlchemy ORM model for the jobs table."""

import uuid
from datetime import datetime
from enum import StrEnum

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    """ORM representation of a persisted job record."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(), primary_key=True)
    job_type: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    parameters: Mapped[dict] = mapped_column(sa.JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.text("NOW()"),
        onupdate=sa.func.now(),
        nullable=False,
    )

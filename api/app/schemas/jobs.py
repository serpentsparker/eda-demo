"""Pydantic schemas for job request/response payloads."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRequest(BaseModel):
    """Payload for submitting a new job."""

    job_type: str = Field(..., description="Logical job type identifier", examples=["echo"])
    parameters: dict[str, str | int | float | bool] = Field(
        default_factory=dict,
        description="Arbitrary job parameters",
    )


class JobResponse(BaseModel):
    """Response returned after job submission or status query."""

    job_id: UUID
    status: JobStatus

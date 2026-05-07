"""Job submission and status endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.events.publisher import publish_job_requested
from app.models.jobs import Job
from app.schemas.jobs import JobRequest, JobResponse, JobStatus

router = APIRouter()


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def submit_job(
    payload: JobRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> JobResponse:
    """Accept a job request, persist it, and emit a JobRequested event to EventBridge."""
    job_id = await publish_job_requested(payload)
    job = Job(
        id=job_id,
        job_type=payload.job_type,
        parameters=payload.parameters,
        status=JobStatus.PENDING,
    )
    session.add(job)
    await session.commit()
    return JobResponse(job_id=job_id, status=JobStatus.PENDING)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> JobResponse:
    """Return the current status of a job."""
    job = await session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(job_id=job.id, status=JobStatus(job.status))

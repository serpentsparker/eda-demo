"""Job submission and status endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.events.publisher import publish_job_requested
from app.schemas.jobs import JobRequest, JobResponse, JobStatus

router = APIRouter()

# In-memory store for demo purposes — replace with a real store in production.
_jobs: dict[str, JobStatus] = {}


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobResponse)
async def submit_job(payload: JobRequest) -> JobResponse:
    """Accept a job request and emit a JobRequested event to EventBridge."""
    job_id = await publish_job_requested(payload)
    _jobs[job_id] = JobStatus.PENDING
    return JobResponse(job_id=job_id, status=JobStatus.PENDING)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """Return the current status of a job."""
    job_status = _jobs.get(job_id)
    if job_status is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(job_id=job_id, status=job_status)

"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routers import health, jobs

app = FastAPI(
    title="EDA Demo API",
    description="Event-driven architecture demo — REST API",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

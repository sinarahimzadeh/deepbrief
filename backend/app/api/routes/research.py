from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.research import ResearchJobCreated, ResearchJobDetail, ResearchRequest
from app.services.quota_guard import gemini_quota_guard
from app.services.research_jobs import research_job_store
from app.services.research_workflow import run_supervisor_job

router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchJobCreated, status_code=status.HTTP_202_ACCEPTED)
async def create_research_job(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResearchJobCreated:
    if not settings.gemini_is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Research is temporarily unavailable",
        )

    if not gemini_quota_guard.status().available:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily research limit reached",
        )

    job = research_job_store.create(request)
    background_tasks.add_task(run_supervisor_job, job.id)
    return ResearchJobCreated(
        id=job.id,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("/{job_id}", response_model=ResearchJobDetail)
async def get_research_job(job_id: str) -> ResearchJobDetail:
    job = research_job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research job not found",
        )
    return job

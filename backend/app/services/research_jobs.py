from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from app.schemas.research import ResearchJobDetail, ResearchPlan, ResearchRequest


class ResearchJobStore:
    """Small in-memory store used until PostgreSQL is added."""

    def __init__(self) -> None:
        self._jobs: dict[str, ResearchJobDetail] = {}
        self._lock = Lock()

    def create(self, request: ResearchRequest) -> ResearchJobDetail:
        now = datetime.now(UTC)
        job = ResearchJobDetail(
            id=str(uuid4()),
            question=request.question,
            max_sources=request.max_sources,
            status="queued",
            current_stage="queued",
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._jobs[job.id] = job
        return job.model_copy(deep=True)

    def get(self, job_id: str) -> ResearchJobDetail | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.model_copy(deep=True) if job is not None else None

    def mark_running(self, job_id: str) -> None:
        self._update(
            job_id,
            status="running",
            current_stage="supervisor",
            error=None,
        )

    def complete_plan(self, job_id: str, plan: ResearchPlan) -> None:
        self._update(
            job_id,
            status="completed",
            current_stage="plan_ready",
            assignments=plan.assignments,
            error=None,
        )

    def fail(self, job_id: str, message: str) -> None:
        self._update(
            job_id,
            status="failed",
            current_stage="failed",
            error=message,
        )

    def reset(self) -> None:
        with self._lock:
            self._jobs.clear()

    def _update(self, job_id: str, **changes: object) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            self._jobs[job_id] = job.model_copy(
                update={**changes, "updated_at": datetime.now(UTC)},
                deep=True,
            )


research_job_store = ResearchJobStore()

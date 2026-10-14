from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from app.schemas.research import (
    ResearchAgentProgress,
    ResearchAgentStatus,
    ResearcherResult,
    ResearchJobDetail,
    ResearchPlan,
    ResearchRequest,
)


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

    def start_researchers(self, job_id: str, plan: ResearchPlan) -> None:
        self._update(
            job_id,
            status="running",
            current_stage="researchers",
            assignments=plan.assignments,
            agents=[
                ResearchAgentProgress(
                    index=assignment.index,
                    title=assignment.title,
                )
                for assignment in plan.assignments
            ],
            error=None,
        )

    def update_agent(
        self,
        job_id: str,
        index: int,
        *,
        status: ResearchAgentStatus,
        message: str,
        sources_found: int | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return

            agents = []
            for agent in job.agents:
                if agent.index != index:
                    agents.append(agent)
                    continue
                agents.append(
                    agent.model_copy(
                        update={
                            "status": status,
                            "progress_message": message,
                            "sources_found": (
                                agent.sources_found
                                if sources_found is None
                                else sources_found
                            ),
                        }
                    )
                )

            self._jobs[job_id] = job.model_copy(
                update={"agents": agents, "updated_at": datetime.now(UTC)},
                deep=True,
            )

    def add_researcher_result(self, job_id: str, result: ResearcherResult) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return

            results = [item for item in job.researcher_results if item.index != result.index]
            results.append(result)
            agents = [
                agent.model_copy(
                    update={
                        "status": "completed",
                        "progress_message": f"Analyzed {len(result.sources)} sources",
                        "sources_found": len(result.sources),
                    }
                )
                if agent.index == result.index
                else agent
                for agent in job.agents
            ]
            self._jobs[job_id] = job.model_copy(
                update={
                    "researcher_results": sorted(results, key=lambda item: item.index),
                    "agents": agents,
                    "updated_at": datetime.now(UTC),
                },
                deep=True,
            )

    def complete_research(self, job_id: str) -> None:
        job = self.get(job_id)
        if job is None or {result.index for result in job.researcher_results} != {1, 2, 3}:
            raise ValueError("A research job requires results from all three researchers")
        self._update(
            job_id,
            status="completed",
            current_stage="research_complete",
            error=None,
        )

    def fail(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            agents = [
                agent.model_copy(
                    update={
                        "status": "failed",
                        "progress_message": "Research stopped",
                    }
                )
                if agent.status not in {"completed", "failed"}
                else agent
                for agent in job.agents
            ]
            self._jobs[job_id] = job.model_copy(
                update={
                    "status": "failed",
                    "current_stage": "failed",
                    "agents": agents,
                    "error": message,
                    "updated_at": datetime.now(UTC),
                },
                deep=True,
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

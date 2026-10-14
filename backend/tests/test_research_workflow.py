import asyncio

import pytest

from app.schemas.research import (
    ResearchAssignment,
    ResearcherResult,
    ResearchFinding,
    ResearchPlan,
    ResearchRequest,
    ResearchSource,
)
from app.services import research_workflow
from app.services.research_jobs import research_job_store
from app.services.web_search import SearchLimitReachedError


def workflow_plan() -> ResearchPlan:
    return ResearchPlan(
        assignments=[
            ResearchAssignment(
                index=index,
                title=f"Research track {index}",
                objective=f"Investigate the evidence for research track number {index}.",
                search_queries=[f"track {index} evidence", f"track {index} sources"],
            )
            for index in range(1, 4)
        ]
    )


def test_langgraph_runs_three_researchers_in_parallel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = workflow_plan()
    started: set[int] = set()
    all_started = asyncio.Event()

    async def fake_plan(question: str) -> ResearchPlan:
        return plan

    async def fake_collect_sources(
        queries: list[str],
        *,
        researcher_index: int,
        max_sources: int,
    ) -> list[ResearchSource]:
        started.add(researcher_index)
        if len(started) == 3:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), timeout=1)
        return [
            ResearchSource(
                source_key=f"R{researcher_index}S1",
                title=f"Source for researcher {researcher_index}",
                url=f"https://example.com/researcher-{researcher_index}",
                domain="example.com",
                snippet="Deterministic evidence used to test parallel graph execution.",
                query=queries[0],
                score=0.9,
            )
        ]

    async def fake_synthesis(
        assignment: ResearchAssignment,
        sources: list[ResearchSource],
    ) -> ResearcherResult:
        return ResearcherResult(
            index=assignment.index,
            title=assignment.title,
            summary="A deterministic synthesis for the parallel workflow test.",
            findings=[
                ResearchFinding(
                    statement="The deterministic source supports this test finding.",
                    source_keys=[sources[0].source_key],
                )
            ],
            sources=sources,
        )

    monkeypatch.setattr(research_workflow, "create_research_plan", fake_plan)
    monkeypatch.setattr(research_workflow, "collect_sources", fake_collect_sources)
    monkeypatch.setattr(research_workflow, "synthesize_research", fake_synthesis)

    research_job_store.reset()
    job = research_job_store.create(
        ResearchRequest(question="Compare three approaches using current evidence.")
    )
    try:
        asyncio.run(asyncio.wait_for(research_workflow.run_research_job(job.id), timeout=2))
        completed = research_job_store.get(job.id)
        assert completed is not None
        assert completed.status == "completed"
        assert completed.current_stage == "research_complete"
        assert started == {1, 2, 3}
        assert len(completed.researcher_results) == 3
    finally:
        research_job_store.reset()


def test_search_limit_failure_is_safe_for_the_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_plan(question: str) -> ResearchPlan:
        return workflow_plan()

    async def exhausted_search(
        queries: list[str],
        *,
        researcher_index: int,
        max_sources: int,
    ) -> list[ResearchSource]:
        raise SearchLimitReachedError("provider details should stay private")

    monkeypatch.setattr(research_workflow, "create_research_plan", fake_plan)
    monkeypatch.setattr(research_workflow, "collect_sources", exhausted_search)

    research_job_store.reset()
    job = research_job_store.create(
        ResearchRequest(question="Compare three approaches using current evidence.")
    )
    try:
        asyncio.run(research_workflow.run_research_job(job.id))
        failed = research_job_store.get(job.id)
        assert failed is not None
        assert failed.status == "failed"
        assert failed.current_stage == "failed"
        assert failed.error == "The free web-search limit has been reached. Please try again later."
        assert "provider details" not in failed.error
    finally:
        research_job_store.reset()

import asyncio

import pytest

from app.schemas.research import (
    ClaimVerification,
    ReportDraft,
    ReportSection,
    ResearchAssignment,
    ResearcherResult,
    ResearchFinding,
    ResearchPlan,
    ResearchRequest,
    ResearchSource,
    VerificationResult,
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


def workflow_report() -> ReportDraft:
    return ReportDraft(
        title="A deterministic research report",
        executive_summary=(
            "The evidence provides a deterministic summary for this workflow test [R1S1]."
        ),
        sections=[
            ReportSection(
                heading="First finding",
                content="The first test source supports this report section [R1S1].",
            ),
            ReportSection(
                heading="Second finding",
                content="The second test source supports this report section [R2S1].",
            ),
        ],
        conclusion="The collected evidence supports the deterministic conclusion [R3S1].",
    )


def workflow_verification() -> VerificationResult:
    return VerificationResult(
        overall_status="passed",
        summary="The checked claims are supported by their cited test sources.",
        claims=[
            ClaimVerification(
                claim="The first test source supports this report section.",
                source_keys=["R1S1"],
                status="supported",
                explanation="The supplied test snippet directly supports the claim.",
            )
        ],
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

    async def fake_report(
        question: str,
        results: list[ResearcherResult],
    ) -> ReportDraft:
        assert question
        assert len(results) == 3
        return workflow_report()

    async def fake_verification(
        report: ReportDraft,
        results: list[ResearcherResult],
    ) -> VerificationResult:
        assert report.title
        assert len(results) == 3
        return workflow_verification()

    monkeypatch.setattr(research_workflow, "create_research_plan", fake_plan)
    monkeypatch.setattr(research_workflow, "collect_sources", fake_collect_sources)
    monkeypatch.setattr(research_workflow, "synthesize_research", fake_synthesis)
    monkeypatch.setattr(research_workflow, "compose_report", fake_report)
    monkeypatch.setattr(research_workflow, "verify_report", fake_verification)

    research_job_store.reset()
    job = research_job_store.create(
        ResearchRequest(question="Compare three approaches using current evidence.")
    )
    try:
        asyncio.run(asyncio.wait_for(research_workflow.run_research_job(job.id), timeout=2))
        completed = research_job_store.get(job.id)
        assert completed is not None
        assert completed.status == "completed"
        assert completed.current_stage == "completed"
        assert started == {1, 2, 3}
        assert len(completed.researcher_results) == 3
        assert completed.report is not None
        assert completed.verification is not None
    finally:
        research_job_store.reset()


def test_report_citations_reject_unknown_source_keys() -> None:
    report = workflow_report().model_copy(
        update={
            "conclusion": "This conclusion cites a source that does not exist [R3S5]."
        }
    )

    with pytest.raises(ValueError, match="invalid source reference"):
        research_workflow.validate_report_citations(
            report,
            {"R1S1", "R2S1", "R3S1"},
        )


def test_report_citations_accept_grouped_source_keys() -> None:
    report = workflow_report().model_copy(
        update={
            "conclusion": "Both test sources support the final conclusion [R2S1, R3S1]."
        }
    )

    research_workflow.validate_report_citations(
        report,
        {"R1S1", "R2S1", "R3S1"},
    )


def test_verification_status_is_derived_from_claim_support() -> None:
    verification = workflow_verification().model_copy(
        update={
            "overall_status": "passed",
            "claims": [
                ClaimVerification(
                    claim="This test claim has only partial support.",
                    source_keys=["R1S1"],
                    status="weak",
                    explanation="The source supports only part of the claim.",
                )
            ],
        }
    )

    normalized = research_workflow.normalize_verification(verification, {"R1S1"})

    assert normalized.overall_status == "completed_with_warnings"
    assert normalized.warnings


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

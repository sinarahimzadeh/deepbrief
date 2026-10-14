import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.routes import research as research_route
from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.research import (
    ClaimVerification,
    ReportDraft,
    ReportSection,
    ResearchAssignment,
    ResearcherResult,
    ResearchFinding,
    ResearchPlan,
    ResearchSource,
    VerificationResult,
)
from app.services.quota_guard import gemini_quota_guard
from app.services.research_jobs import research_job_store


def sample_plan() -> ResearchPlan:
    return ResearchPlan(
        assignments=[
            ResearchAssignment(
                index=1,
                title="Market and pricing",
                objective="Compare current products, plans, and total ownership costs.",
                search_queries=["AI coding assistant pricing", "coding assistant enterprise plans"],
            ),
            ResearchAssignment(
                index=2,
                title="Security and privacy",
                objective="Examine data handling, retention, and enterprise security controls.",
                search_queries=["AI coding assistant privacy", "coding assistant data retention"],
            ),
            ResearchAssignment(
                index=3,
                title="Developer experience",
                objective="Evaluate supported workflows, integrations, and reported code quality.",
                search_queries=["AI coding assistant IDE support", "coding assistant code quality"],
            ),
        ]
    )


def sample_result(assignment: ResearchAssignment) -> ResearcherResult:
    source_key = f"R{assignment.index}S1"
    return ResearcherResult(
        index=assignment.index,
        title=assignment.title,
        summary="The available evidence supports a concise test research summary.",
        findings=[
            ResearchFinding(
                statement="The test evidence supports this researcher finding.",
                source_keys=[source_key],
            )
        ],
        sources=[
            ResearchSource(
                source_key=source_key,
                title="Example evidence",
                url=f"https://example.com/source-{assignment.index}",
                domain="example.com",
                snippet="A useful evidence snippet for the deterministic API test.",
                query=assignment.search_queries[0],
                score=0.9,
            )
        ],
    )


def sample_report() -> ReportDraft:
    return ReportDraft(
        title="A deterministic API research report",
        executive_summary="The test evidence supports this API report summary [R1S1].",
        sections=[
            ReportSection(
                heading="Market evidence",
                content="The market finding is supported by the first source [R1S1].",
            ),
            ReportSection(
                heading="Technical evidence",
                content="The technical finding is supported by the second source [R2S1].",
            ),
        ],
        conclusion="The test evidence supports the final API conclusion [R3S1].",
    )


def sample_verification() -> VerificationResult:
    return VerificationResult(
        overall_status="passed",
        summary="The important report claims are supported by their citations.",
        claims=[
            ClaimVerification(
                claim="The market finding is supported by the first source.",
                source_keys=["R1S1"],
                status="supported",
                explanation="The source directly supports the test claim.",
            )
        ],
    )


def test_research_plan_requires_exactly_three_assignments() -> None:
    with pytest.raises(ValidationError):
        ResearchPlan(assignments=sample_plan().assignments[:2])


def test_research_job_creates_exactly_three_assignments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-google-key",
        gemini_model="gemini-test-lite",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    research_job_store.reset()
    gemini_quota_guard.reset()

    async def fake_research_job(job_id: str) -> None:
        research_job_store.mark_running(job_id)
        plan = sample_plan()
        research_job_store.start_researchers(job_id, plan)
        for assignment in plan.assignments:
            research_job_store.add_researcher_result(job_id, sample_result(assignment))
        research_job_store.start_writer(job_id)
        research_job_store.finish_writer(job_id, sample_report())
        research_job_store.start_verifier(job_id)
        research_job_store.complete_research(job_id, sample_verification())

    monkeypatch.setattr(research_route, "run_research_job", fake_research_job)

    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/research",
                json={
                    "question": "Which AI coding assistant should a small team choose?",
                    "max_sources": 12,
                },
            )
            assert created.status_code == 202

            job = await client.get(f"/api/v1/research/{created.json()['id']}")

        assert job.status_code == 200
        body = job.json()
        assert body["status"] == "completed"
        assert body["current_stage"] == "completed"
        assert len(body["assignments"]) == 3
        assert {assignment["index"] for assignment in body["assignments"]} == {1, 2, 3}
        assert len(body["researcher_results"]) == 3
        assert all(agent["status"] == "completed" for agent in body["agents"])
        assert body["report"]["title"] == "A deterministic API research report"
        assert body["verification"]["overall_status"] == "passed"

    try:
        asyncio.run(make_request())
    finally:
        research_job_store.reset()
        gemini_quota_guard.reset()
        app.dependency_overrides.clear()


def test_research_job_rejects_missing_model_configuration() -> None:
    settings = Settings(_env_file=None, google_api_key=None)
    app.dependency_overrides[get_settings] = lambda: settings

    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/research",
                json={"question": "A sufficiently long research question"},
            )

        assert response.status_code == 503
        assert "GOOGLE_API_KEY" not in response.text

    try:
        asyncio.run(make_request())
    finally:
        app.dependency_overrides.clear()


def test_research_job_honors_daily_quota_pause() -> None:
    settings = Settings(_env_file=None, google_api_key="test-google-key")
    app.dependency_overrides[get_settings] = lambda: settings
    gemini_quota_guard.disable_until_next_reset()

    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/research",
                json={"question": "A sufficiently long research question"},
            )

        assert response.status_code == 429

    try:
        asyncio.run(make_request())
    finally:
        gemini_quota_guard.reset()
        app.dependency_overrides.clear()


def test_research_job_validates_question_length() -> None:
    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/research",
                json={"question": "too short"},
            )

        assert response.status_code == 422

    asyncio.run(make_request())


def test_unknown_research_job_returns_not_found() -> None:
    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/research/unknown")

        assert response.status_code == 404

    asyncio.run(make_request())

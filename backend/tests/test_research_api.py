import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.routes import research as research_route
from app.core.config import Settings, get_settings
from app.main import app
from app.schemas.research import ResearchAssignment, ResearchPlan
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

    async def fake_supervisor(job_id: str) -> None:
        research_job_store.mark_running(job_id)
        research_job_store.complete_plan(job_id, sample_plan())

    monkeypatch.setattr(research_route, "run_supervisor_job", fake_supervisor)

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
        assert body["current_stage"] == "plan_ready"
        assert len(body["assignments"]) == 3
        assert {assignment["index"] for assignment in body["assignments"]} == {1, 2, 3}

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

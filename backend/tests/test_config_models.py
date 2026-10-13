import asyncio

from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, get_settings
from app.main import app
from app.services.quota_guard import gemini_quota_guard


def test_model_config_returns_public_allowlist_without_secrets() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-google-key",
        gemini_model="gemini-test-lite",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    gemini_quota_guard.reset()

    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/config/models")

        assert response.status_code == 200
        assert response.json() == {
            "provider": "google_genai",
            "label": "Google Gemini",
            "model": "gemini-test-lite",
            "configured": True,
            "available": True,
            "disabled_reason": None,
            "disabled_until": None,
        }
        assert "test-google-key" not in response.text

    try:
        asyncio.run(make_request())
    finally:
        gemini_quota_guard.reset()
        app.dependency_overrides.clear()


def test_model_config_reports_daily_quota_pause() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key="test-google-key",
        gemini_model="gemini-test-lite",
    )
    app.dependency_overrides[get_settings] = lambda: settings
    gemini_quota_guard.disable_until_next_reset()

    async def make_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/config/models")

        body = response.json()
        assert response.status_code == 200
        assert body["available"] is False
        assert body["disabled_reason"] == "Gemini free daily quota reached"
        assert body["disabled_until"] is not None

    try:
        asyncio.run(make_request())
    finally:
        gemini_quota_guard.reset()
        app.dependency_overrides.clear()

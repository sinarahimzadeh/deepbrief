import pytest

from app.core.config import Settings
from app.services import llm_factory
from app.services.llm_factory import ModelConfigurationError, create_chat_model


def test_factory_requires_gemini_key() -> None:
    settings = Settings(
        _env_file=None,
        google_api_key=None,
        gemini_model="gemini-test-lite",
    )

    with pytest.raises(ModelConfigurationError, match="GOOGLE_API_KEY"):
        create_chat_model(settings=settings)


def test_factory_builds_fixed_gemini_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_model(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(llm_factory, "ChatGoogleGenerativeAI", fake_model)
    settings = Settings(
        _env_file=None,
        google_api_key="google-secret",
        gemini_model="gemini-test-lite",
        llm_timeout_seconds=45,
        llm_max_retries=2,
    )

    result = create_chat_model(settings=settings)

    assert result is not None
    assert captured["model"] == "gemini-test-lite"
    assert "temperature" not in captured
    assert captured["request_timeout"] == 45
    assert captured["retries"] == 2
    assert captured["api_key"] == "google-secret"

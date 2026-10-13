from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import Settings, get_settings


class ModelConfigurationError(ValueError):
    """Raised when a requested model cannot be created safely."""


def _secret_value(settings: Settings) -> str:
    key = settings.google_api_key
    if key is None or not key.get_secret_value().strip():
        raise ModelConfigurationError("GOOGLE_API_KEY is not configured")
    return key.get_secret_value()


def create_chat_model(
    temperature: float = 0,
    *,
    settings: Settings | None = None,
) -> BaseChatModel:
    """Create DeepBrief's fixed Gemini model through LangChain."""

    app_settings = settings or get_settings()
    api_key = _secret_value(app_settings)

    return ChatGoogleGenerativeAI(
        api_key=api_key,
        model=app_settings.gemini_model,
        temperature=temperature,
        request_timeout=app_settings.llm_timeout_seconds,
        retries=app_settings.llm_max_retries,
    )

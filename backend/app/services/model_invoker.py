from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

from app.services.quota_guard import (
    DailyQuotaExhaustedError,
    gemini_quota_guard,
    is_daily_quota_error,
)


async def invoke_chat_model(
    model: BaseChatModel,
    model_input: Any,
    **kwargs: Any,
) -> BaseMessage:
    """Invoke Gemini with DeepBrief's daily free-quota circuit breaker."""

    gemini_quota_guard.raise_if_disabled()
    try:
        return await model.ainvoke(model_input, **kwargs)
    except Exception as error:
        if not is_daily_quota_error(error):
            raise

        disabled_until = gemini_quota_guard.disable_until_next_reset()
        raise DailyQuotaExhaustedError(disabled_until) from error

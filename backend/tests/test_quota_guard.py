import asyncio
from datetime import UTC, datetime

import pytest

from app.services.model_invoker import invoke_chat_model
from app.services.quota_guard import (
    DailyQuotaExhaustedError,
    GeminiQuotaGuard,
    gemini_quota_guard,
    is_daily_quota_error,
)


class FailingModel:
    async def ainvoke(self, model_input: object, **kwargs: object) -> object:
        del model_input, kwargs
        raise RuntimeError(
            "429 RESOURCE_EXHAUSTED: quota GenerateRequestsPerDayPerProjectPerModel-FreeTier"
        )


def test_guard_disables_until_midnight_pacific_and_then_reopens() -> None:
    guard = GeminiQuotaGuard()
    now = datetime(2026, 7, 10, 18, 0, tzinfo=UTC)

    disabled_until = guard.disable_until_next_reset(now)

    assert disabled_until == datetime(2026, 7, 11, 7, 0, tzinfo=UTC)
    assert guard.status(now).available is False
    assert guard.status(disabled_until).available is True


def test_daily_quota_detection_ignores_per_minute_limit() -> None:
    daily = RuntimeError(
        "429 quota exceeded: GenerateRequestsPerDayPerProjectPerModel-FreeTier"
    )
    per_minute = RuntimeError(
        "429 quota exceeded: GenerateRequestsPerMinutePerProjectPerModel-FreeTier"
    )

    assert is_daily_quota_error(daily) is True
    assert is_daily_quota_error(per_minute) is False


def test_invoker_opens_daily_quota_circuit_breaker() -> None:
    gemini_quota_guard.reset()

    async def invoke() -> None:
        with pytest.raises(DailyQuotaExhaustedError):
            await invoke_chat_model(FailingModel(), "hello")  # type: ignore[arg-type]

    try:
        asyncio.run(invoke())
        assert gemini_quota_guard.status().available is False
    finally:
        gemini_quota_guard.reset()

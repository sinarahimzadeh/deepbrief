from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from threading import Lock
from zoneinfo import ZoneInfo

PACIFIC_TIME = ZoneInfo("America/Los_Angeles")
DAILY_QUOTA_REASON = "Gemini free daily quota reached"


@dataclass(frozen=True)
class QuotaStatus:
    available: bool
    disabled_until: datetime | None = None
    reason: str | None = None


class DailyQuotaExhaustedError(RuntimeError):
    """Raised when Gemini is paused until the next free-quota reset."""

    def __init__(self, disabled_until: datetime) -> None:
        self.disabled_until = disabled_until
        super().__init__(
            f"{DAILY_QUOTA_REASON}. Try again after {disabled_until.isoformat()}."
        )


def _as_utc(value: datetime | None = None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        return current.replace(tzinfo=UTC)
    return current.astimezone(UTC)


def is_daily_quota_error(error: Exception) -> bool:
    """Identify Google's daily quota errors without treating RPM errors as daily."""

    message = f"{type(error).__name__}: {error}".lower().replace("_", " ")
    quota_markers = ("429", "quota", "rate limit", "resource exhausted")
    daily_markers = (
        "daily",
        "per day",
        "perday",
        "requests/day",
        "request per day",
        "rpd",
    )
    return any(marker in message for marker in quota_markers) and any(
        marker in message for marker in daily_markers
    )


class GeminiQuotaGuard:
    """Fail closed after a daily quota response, then reopen at midnight Pacific."""

    def __init__(self) -> None:
        self._disabled_until: datetime | None = None
        self._lock = Lock()

    @staticmethod
    def next_reset(now: datetime | None = None) -> datetime:
        current_pacific = _as_utc(now).astimezone(PACIFIC_TIME)
        next_date = current_pacific.date() + timedelta(days=1)
        return datetime.combine(next_date, time.min, PACIFIC_TIME).astimezone(UTC)

    def disable_until_next_reset(self, now: datetime | None = None) -> datetime:
        disabled_until = self.next_reset(now)
        with self._lock:
            self._disabled_until = disabled_until
        return disabled_until

    def status(self, now: datetime | None = None) -> QuotaStatus:
        current = _as_utc(now)
        with self._lock:
            if self._disabled_until is not None and current >= self._disabled_until:
                self._disabled_until = None
            disabled_until = self._disabled_until

        if disabled_until is None:
            return QuotaStatus(available=True)
        return QuotaStatus(
            available=False,
            disabled_until=disabled_until,
            reason=DAILY_QUOTA_REASON,
        )

    def raise_if_disabled(self, now: datetime | None = None) -> None:
        status = self.status(now)
        if not status.available and status.disabled_until is not None:
            raise DailyQuotaExhaustedError(status.disabled_until)

    def reset(self) -> None:
        with self._lock:
            self._disabled_until = None


gemini_quota_guard = GeminiQuotaGuard()

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings for the DeepBrief API."""

    frontend_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    google_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.5-flash-lite"

    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @staticmethod
    def _split_csv(value: str) -> tuple[str, ...]:
        return tuple(item.strip() for item in value.split(",") if item.strip())

    @property
    def frontend_origin_list(self) -> list[str]:
        return list(self._split_csv(self.frontend_origins))

    @property
    def gemini_is_configured(self) -> bool:
        key = self.google_api_key
        return key is not None and bool(key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()

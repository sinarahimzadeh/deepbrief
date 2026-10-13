from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ProviderId = Literal["google_genai"]


class ModelConfigResponse(BaseModel):
    provider: ProviderId = "google_genai"
    label: str
    model: str
    configured: bool
    available: bool
    disabled_reason: str | None = None
    disabled_until: datetime | None = None

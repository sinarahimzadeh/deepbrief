from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.config import ModelConfigResponse
from app.services.quota_guard import gemini_quota_guard

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("/models", response_model=ModelConfigResponse)
async def list_models(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ModelConfigResponse:
    quota_status = gemini_quota_guard.status()
    configured = settings.gemini_is_configured
    return ModelConfigResponse(
        label="Google Gemini",
        model=settings.gemini_model,
        configured=configured,
        available=configured and quota_status.available,
        disabled_reason=quota_status.reason,
        disabled_until=quota_status.disabled_until,
    )

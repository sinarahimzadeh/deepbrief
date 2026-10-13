from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="DeepBrief API",
    description="Backend API for the DeepBrief multi-agent research platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"name": "DeepBrief API", "docs": "/docs"}


"""ClauseTrace FastAPI application entrypoint."""

from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.workspaces import router as workspaces_router
from app.api.courtroom import router as courtroom_router

app = FastAPI(
    title="ClauseTrace API",
    version="2.0.0",
    description="Evidence-grounded contract and policy verification engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspaces_router)
app.include_router(courtroom_router)


@app.get("/api/v1/health")
async def health_check() -> Dict[str, Any]:
    """Return API health status and model configuration."""
    return {
        "status": "ok",
        "service": "clausetrace-api",
        "version": "2.0.0",
        "llm_provider": "meta-llama",
        "primary_model": settings.META_PRIMARY_MODEL,
        "api_key_configured": bool(
            settings.META_API_KEY
            and settings.META_API_KEY != "your_meta_model_api_key_here"
        ),
    }

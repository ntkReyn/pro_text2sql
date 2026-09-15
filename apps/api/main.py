from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from apps.api.routes.semantic import create_semantic_router


APP_NAME = os.getenv("APP_NAME", "pro-text2sql")
APP_ENV = os.getenv("APP_ENV", "local")

app = FastAPI(
    title="Agentic Analytics & Semantic Text-to-SQL",
    version="0.1.0",
)
app.include_router(create_semantic_router(APP_ENV))


def _is_configured(name: str) -> bool:
    value = os.getenv(name, "").strip()
    placeholders = ("CHANGE_ME", "PROJECT_REF", "POOLER_HOST", "YOUR_")
    return bool(value) and not any(marker in value for marker in placeholders)


def _model_is_cached(model_id: str) -> bool:
    cache_root = Path(os.getenv("HF_HOME", "/opt/huggingface")) / "hub"
    cache_name = "models--" + model_id.replace("/", "--")
    return (cache_root / cache_name / "snapshots").is_dir()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "environment": APP_ENV,
        "status": "running",
        "api_docs": "/docs",
    }


@app.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def readiness() -> JSONResponse:
    embedding_model = os.getenv(
        "EMBEDDING_MODEL", "AITeamVN/Vietnamese_Embedding"
    )
    reranker_model = os.getenv(
        "RERANKER_MODEL", "AITeamVN/Vietnamese_Reranker"
    )
    checks = {
        "analytics_database": _is_configured("ANALYTICS_DATABASE_URL"),
        "llm_api_key": _is_configured("LLM_API_KEY"),
        "embedding_cache": _model_is_cached(embedding_model),
        "reranker_cache": _model_is_cached(reranker_model),
    }
    ready = all(checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "checks": checks,
        },
    )

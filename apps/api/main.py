from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from apps.api.routes.semantic import create_semantic_router
from packages.integrations import WrenSettings

APP_NAME = os.getenv("APP_NAME", "pro-text2sql")
APP_ENV = os.getenv("APP_ENV", "local")

app = FastAPI(
    title="Wren-first Text-to-SQL",
    version="0.1.0",
)
app.include_router(create_semantic_router(APP_ENV))


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
    settings = WrenSettings.from_env()
    checks = {
        "wren_project": settings.wren_configured,
        "llm_api_key": settings.llm_configured,
        "analytics_database": settings.database_configured,
    }
    ready = all(checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "checks": checks,
        },
    )

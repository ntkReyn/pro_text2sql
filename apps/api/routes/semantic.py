"""Developer-facing endpoints for the first semantic Text-to-SQL slice."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from packages.analytics_engine.sql_generation import PostgreSQLSemanticCompiler
from packages.analytics_engine.validation import SemanticPlanValidationError
from packages.domain import SQLCandidate, SemanticQueryPlan
from packages.semantic_layer import load_default_catalog


class MetricSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    version: str
    status: str
    label: str
    description: str
    unit: str
    allowed_dimensions: list[str]


def create_semantic_router(app_env: str) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["semantic-query"])
    catalog = load_default_catalog()
    compiler = PostgreSQLSemanticCompiler(catalog)
    allow_draft_metrics = app_env in {"local", "test"}

    @router.get("/catalog/metrics", response_model=list[MetricSummary])
    def list_metrics() -> list[MetricSummary]:
        return [
            MetricSummary(
                id=metric.id,
                version=metric.version,
                status=metric.status.value,
                label=metric.label,
                description=metric.description,
                unit=metric.unit,
                allowed_dimensions=metric.allowed_dimensions,
            )
            for metric in catalog.metrics
        ]

    @router.post("/query/compile", response_model=SQLCandidate)
    def compile_semantic_plan(plan: SemanticQueryPlan) -> SQLCandidate:
        """Compile a supplied plan; this endpoint never executes SQL."""

        try:
            return compiler.compile(
                plan,
                allow_draft_metrics=allow_draft_metrics,
            )
        except SemanticPlanValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    return router

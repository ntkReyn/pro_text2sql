"""Wren-first text-to-SQL API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from packages.analytics_engine.validation import WrenSQLSecurityValidator
from packages.analytics_engine.wren_memory import WrenMemoryService, WrenMemoryStatus
from packages.analytics_engine.wren_runtime import (
    WrenCubeDetail,
    WrenCubeQuery,
    WrenCubeQueryResponse,
    WrenCubeService,
    WrenCubeSummary,
    WrenDryRunResponse,
    WrenNativeRuntime,
    WrenOperationError,
    WrenPlanResponse,
)
from packages.analytics_engine.wren_workflow import (
    WrenFirstWorkflow,
    WrenModelSummary,
    WrenProjectContext,
    WrenQueryResponse,
)
from packages.integrations import WrenSettings


class WrenQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=10_000)
    execute: bool = False


class WrenSQLRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sql: str = Field(min_length=1, max_length=100_000)


class WrenMemoryFetchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=10_000)
    limit: int = Field(default=5, ge=1, le=50)
    item_type: str | None = Field(default=None, max_length=64)
    model_name: str | None = Field(default=None, max_length=256)
    threshold: int | None = Field(default=None, ge=1_000, le=200_000)


class WrenMemoryRecallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=10_000)
    limit: int = Field(default=3, ge=1, le=50)
    datasource: str | None = Field(default=None, max_length=256)


class WrenMemoryStoreRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nl: str = Field(min_length=1, max_length=10_000)
    sql: str = Field(min_length=1, max_length=100_000)
    datasource: str | None = Field(default=None, max_length=256)
    tags: list[str] = Field(default_factory=list, max_length=20)


class WrenCubeRequest(WrenCubeQuery):
    execute: bool = False


def create_semantic_router(
    app_env: str,
    *,
    wren_settings: WrenSettings | None = None,
    workflow: WrenFirstWorkflow | None = None,
) -> APIRouter:
    del app_env  # The Wren project, not an application environment, owns semantics.
    router = APIRouter(prefix="/api/v1", tags=["wren-query"])
    settings = wren_settings or WrenSettings.from_env()
    wren_workflow = workflow or WrenFirstWorkflow(settings)
    cube_service = WrenCubeService()
    runtime = WrenNativeRuntime()
    validator = WrenSQLSecurityValidator(max_rows=settings.wren_max_sql_rows)

    def project_context(question: str | None = None) -> WrenProjectContext:
        return WrenProjectContext(
            settings.wren_project_path,
            memory_backend=settings.wren_memory_backend,
            memory_path=settings.wren_memory_path or None,
            memory_schema_threshold=settings.wren_memory_schema_threshold,
        )

    def memory_service() -> WrenMemoryService:
        return WrenMemoryService(
            settings.wren_project_path,
            backend=settings.wren_memory_backend,
            memory_path=settings.wren_memory_path or None,
            schema_threshold=settings.wren_memory_schema_threshold,
        )

    def operation_error(exc: WrenOperationError) -> HTTPException:
        status = 503 if exc.code in {
            "database_not_configured",
            "wren_dry_run_failed",
            "wren_query_failed",
        } else 422
        return HTTPException(
            status_code=status,
            detail={
                "code": exc.code,
                "phase": exc.phase,
                "message": exc.message,
                "retryable": exc.retryable,
            },
        )

    def validated_plan(sql: str) -> tuple[Any, str, Any]:
        try:
            context = project_context().load()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_context_unavailable") from exc
        logical_report = validator.inspect(sql, context.manifest, stage="logical")
        if logical_report.decision.value != "pass":
            raise HTTPException(
                status_code=422,
                detail={"code": logical_report.error_code, "phase": "sql_policy"},
            )
        try:
            planned_sql = runtime.dry_plan(context.manifest, sql)
        except WrenOperationError as exc:
            raise operation_error(exc) from exc
        expanded_report = validator.inspect(
            planned_sql,
            context.manifest,
            stage="expanded",
        )
        if expanded_report.decision.value != "pass":
            raise HTTPException(
                status_code=422,
                detail={"code": expanded_report.error_code, "phase": "sql_policy"},
            )
        return context, planned_sql, expanded_report

    @router.get("/wren/models", response_model=list[WrenModelSummary])
    def list_wren_models() -> list[WrenModelSummary]:
        """List the logical models exposed by the active Wren project."""

        try:
            return project_context().load().summary.models
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="wren_context_unavailable",
            ) from exc

    @router.post("/query/wren", response_model=WrenQueryResponse)
    async def query_with_wren(request: WrenQuestion) -> WrenQueryResponse:
        """Answer a natural-language question through the Wren workflow."""

        if request.execute and not settings.analytics_execution_enabled:
            raise HTTPException(status_code=503, detail="execution_disabled")
        return await wren_workflow.run(request.question.strip(), execute=request.execute)

    @router.get("/wren/cubes", response_model=list[WrenCubeSummary])
    def list_wren_cubes() -> list[WrenCubeSummary]:
        try:
            return cube_service.list_cubes(project_context().load().manifest)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_context_unavailable") from exc

    @router.get("/wren/cubes/{name}", response_model=WrenCubeDetail)
    def describe_wren_cube(name: str) -> WrenCubeDetail:
        try:
            return cube_service.describe_cube(project_context().load().manifest, name)
        except WrenOperationError as exc:
            raise operation_error(exc) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_context_unavailable") from exc

    @router.post("/wren/dry-plan", response_model=WrenPlanResponse)
    def dry_plan_wren(request: WrenSQLRequest) -> WrenPlanResponse:
        context, planned_sql, report = validated_plan(request.sql.strip())
        del context
        return WrenPlanResponse(
            status="planned",
            sql=request.sql.strip(),
            planned_sql=planned_sql,
            security=report,
        )

    @router.post("/wren/dry-run", response_model=WrenDryRunResponse)
    def dry_run_wren(request: WrenSQLRequest) -> WrenDryRunResponse:
        if not settings.analytics_execution_enabled:
            raise HTTPException(status_code=503, detail="execution_disabled")
        if not settings.database_configured:
            raise HTTPException(status_code=503, detail="database_not_configured")
        context, planned_sql, report = validated_plan(request.sql.strip())
        try:
            runtime.dry_run(
                context.manifest,
                request.sql.strip(),
                database_url=settings.analytics_database_url,
                statement_timeout_ms=settings.analytics_database_statement_timeout_ms,
            )
        except WrenOperationError as exc:
            raise operation_error(exc) from exc
        return WrenDryRunResponse(
            status="validated",
            sql=request.sql.strip(),
            planned_sql=planned_sql,
            security=report,
        )

    @router.post("/wren/query/cube", response_model=WrenCubeQueryResponse)
    def query_wren_cube(request: WrenCubeRequest) -> WrenCubeQueryResponse:
        if request.execute and not settings.analytics_execution_enabled:
            raise HTTPException(status_code=503, detail="execution_disabled")
        query = WrenCubeQuery.model_validate(request.model_dump(exclude={"execute"}))
        if query.limit is None:
            query = query.model_copy(update={"limit": settings.wren_max_sql_rows})
        try:
            context = project_context().load().manifest
            logical_sql = cube_service.to_sql(context, query)
            logical_report = validator.inspect(logical_sql, context, stage="logical")
            if logical_report.decision.value != "pass":
                raise HTTPException(
                    status_code=422,
                    detail={"code": logical_report.error_code, "phase": "sql_policy"},
                )
            planned_sql = runtime.dry_plan(context, logical_sql)
        except WrenOperationError as exc:
            raise operation_error(exc) from exc
        expanded_report = validator.inspect(planned_sql, context, stage="expanded")
        if expanded_report.decision.value != "pass":
            raise HTTPException(
                status_code=422,
                detail={"code": expanded_report.error_code, "phase": "sql_policy"},
            )
        execution = None
        status = "planned"
        if request.execute:
            if not settings.database_configured:
                raise HTTPException(status_code=503, detail="database_not_configured")
            try:
                execution = runtime.query(
                    context,
                    logical_sql,
                    database_url=settings.analytics_database_url,
                    max_rows=settings.wren_max_sql_rows,
                    statement_timeout_ms=settings.analytics_database_statement_timeout_ms,
                )
            except WrenOperationError as exc:
                raise operation_error(exc) from exc
            status = "executed"
        return WrenCubeQueryResponse(
            status=status,
            query=query,
            sql=logical_sql,
            planned_sql=planned_sql,
            security=expanded_report,
            execution=execution,
            no_rows_returned=execution is None,
        )

    @router.get("/wren/memory/status", response_model=WrenMemoryStatus)
    def memory_status() -> WrenMemoryStatus:
        try:
            snapshot = project_context().load()
            return memory_service().status(snapshot.manifest)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.get("/wren/memory/describe")
    def describe_memory() -> dict[str, str]:
        try:
            manifest = project_context().load().manifest
            return {"schema": WrenMemoryService.describe_schema(manifest)}
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.get("/wren/memory/queries")
    def list_memory_queries(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        try:
            from wren.memory.markdown import load_query_pairs

            pairs = load_query_pairs(project_context().load().project_path)
            return {
                "items": pairs[offset : offset + limit],
                "total": len(pairs),
                "source": "knowledge/sql/*.md",
            }
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.post("/wren/memory/index")
    def index_memory() -> dict[str, Any]:
        try:
            manifest = project_context().load().manifest
            return memory_service().index(manifest)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.post("/wren/memory/reset")
    def reset_memory() -> dict[str, str]:
        """Reset only the derived memory index; Markdown source remains."""
        try:
            memory_service().reset()
            return {"status": "reset", "source": "knowledge/sql/*.md"}
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.post("/wren/memory/fetch")
    def fetch_memory(request: WrenMemoryFetchRequest) -> dict[str, Any]:
        try:
            manifest = project_context().load().manifest
            return memory_service().fetch(
                manifest,
                request.query,
                limit=request.limit,
                item_type=request.item_type,
                model_name=request.model_name,
                threshold=request.threshold,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.post("/wren/memory/recall")
    def recall_memory(request: WrenMemoryRecallRequest) -> list[dict[str, Any]]:
        try:
            return memory_service().recall(
                request.query,
                limit=request.limit,
                datasource=request.datasource,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    @router.post("/wren/memory/store")
    def store_memory(request: WrenMemoryStoreRequest) -> dict[str, Any]:
        context, _, _ = validated_plan(request.sql.strip())
        try:
            result = memory_service().store(
                request.nl.strip(),
                request.sql.strip(),
                datasource=request.datasource,
                tags=request.tags,
            )
            result["validated_against"] = context.project_path.name
            return result
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail="wren_memory_unavailable") from exc

    return router

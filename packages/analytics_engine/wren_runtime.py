"""Native Wren runtime adapters for plan, dry-run and structured cubes."""

from __future__ import annotations

import base64
import json
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from packages.domain import QueryExecutionResult, SQLSecurityReport


class WrenOperationError(RuntimeError):
    """Safe, structured operation error modelled after WrenError."""

    def __init__(
        self,
        code: str,
        phase: str,
        message: str,
        *,
        retryable: bool = False,
    ) -> None:
        self.code = code
        self.phase = phase
        self.retryable = retryable
        self.message = message
        super().__init__(message)


class WrenCubeFilter(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    dimension: str = Field(min_length=1, max_length=256)
    operator: str = Field(min_length=1, max_length=32)
    value: Any | None = None


class WrenCubeTimeDimension(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    dimension: str = Field(min_length=1, max_length=256)
    granularity: str = Field(min_length=1, max_length=32)
    date_range: list[str] | None = Field(default=None, alias="dateRange")


class WrenCubeOrderBy(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    member: str = Field(min_length=1, max_length=256)
    direction: Literal["asc", "desc"]


class WrenCubeQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    cube: str = Field(min_length=1, max_length=256)
    measures: list[str] = Field(min_length=1, max_length=50)
    dimensions: list[str] = Field(default_factory=list, max_length=50)
    time_dimensions: list[WrenCubeTimeDimension] = Field(
        default_factory=list,
        alias="timeDimensions",
    )
    filters: list[WrenCubeFilter] = Field(default_factory=list, max_length=50)
    order_by: list[WrenCubeOrderBy] = Field(
        default_factory=list,
        alias="orderBy",
    )
    limit: int | None = Field(default=None, ge=1, le=10_000)
    offset: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def reject_duplicates(self) -> WrenCubeQuery:
        for name, values in (
            ("measures", self.measures),
            ("dimensions", self.dimensions),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate cube {name} are not allowed")
        return self


class WrenCubeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    base_object: str | None = None
    description: str | None = None
    measures: list[str] = Field(default_factory=list)
    dimensions: list[str] = Field(default_factory=list)
    time_dimensions: list[str] = Field(default_factory=list)


class WrenCubeDetail(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    name: str
    base_object: str | None = None
    measures: list[dict[str, Any]] = Field(default_factory=list)
    dimensions: list[dict[str, Any]] = Field(default_factory=list)
    time_dimensions: list[dict[str, Any]] = Field(default_factory=list)
    hierarchies: dict[str, list[str]] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)


class WrenCubeQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    query: WrenCubeQuery
    sql: str
    planned_sql: str
    security: SQLSecurityReport
    execution: QueryExecutionResult | None = None
    no_rows_returned: bool = True


class WrenPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    sql: str
    planned_sql: str
    security: SQLSecurityReport
    no_rows_returned: bool = True


class WrenDryRunResponse(WrenPlanResponse):
    status: str = "validated"


class WrenNativeRuntime:
    """Small adapter that intentionally calls WrenEngine, not a second planner."""

    @staticmethod
    def _manifest_string(manifest: dict[str, Any]) -> str:
        return base64.b64encode(
            json.dumps(manifest, ensure_ascii=False).encode("utf-8")
        ).decode("ascii")

    def dry_plan(self, manifest: dict[str, Any], sql: str) -> str:
        try:
            from wren import DataSource, WrenEngine

            with WrenEngine(
                self._manifest_string(manifest),
                DataSource.postgres,
                {},
                fallback=False,
            ) as engine:
                return engine.dry_plan(sql)
        except WrenOperationError:
            raise
        except Exception as exc:
            raise WrenOperationError(
                "wren_dry_plan_failed",
                "sql_planning",
                _safe_error(exc),
            ) from exc

    def dry_run(
        self,
        manifest: dict[str, Any],
        sql: str,
        *,
        database_url: str,
        statement_timeout_ms: int = 15_000,
    ) -> str:
        if not database_url:
            raise WrenOperationError(
                "database_not_configured",
                "sql_dry_run",
                "a database connection is required for Wren dry_run",
            )
        try:
            from wren import DataSource, WrenEngine

            connection_info = _connection_info(database_url, statement_timeout_ms)
            with WrenEngine(
                self._manifest_string(manifest),
                DataSource.postgres,
                connection_info,
                fallback=False,
            ) as engine:
                planned_sql = engine.dry_plan(sql)
                engine.dry_run(sql)
                return planned_sql
        except WrenOperationError:
            raise
        except Exception as exc:
            raise WrenOperationError(
                "wren_dry_run_failed",
                "sql_dry_run",
                _safe_error(exc),
            ) from exc

    def query(
        self,
        manifest: dict[str, Any],
        sql: str,
        *,
        database_url: str,
        max_rows: int,
        statement_timeout_ms: int = 15_000,
    ) -> QueryExecutionResult:
        if not database_url:
            raise WrenOperationError(
                "database_not_configured",
                "sql_execution",
                "a database connection is required for Wren query",
            )
        started = perf_counter()
        try:
            from wren import DataSource, WrenEngine

            connection_info = _connection_info(database_url, statement_timeout_ms)
            with WrenEngine(
                self._manifest_string(manifest),
                DataSource.postgres,
                connection_info,
                fallback=False,
            ) as engine:
                table = engine.query(sql, limit=max_rows + 1)
            rows = table.to_pylist()
            truncated = len(rows) > max_rows
            return QueryExecutionResult(
                columns=list(table.column_names),
                rows=rows[:max_rows],
                row_count=min(len(rows), max_rows),
                truncated=truncated,
                duration_ms=max(0, round((perf_counter() - started) * 1000)),
            )
        except WrenOperationError:
            raise
        except Exception as exc:
            raise WrenOperationError(
                "wren_query_failed",
                "sql_execution",
                _safe_error(exc),
            ) from exc


class WrenCubeService:
    """Build CubeQuery SQL through the installed Wren core library."""

    @staticmethod
    def list_cubes(manifest: dict[str, Any]) -> list[WrenCubeSummary]:
        result: list[WrenCubeSummary] = []
        for cube in manifest.get("cubes", []) or []:
            if not isinstance(cube, dict) or not cube.get("name"):
                continue
            props = cube.get("properties") or {}
            result.append(
                WrenCubeSummary(
                    name=str(cube["name"]),
                    base_object=cube.get("baseObject") or cube.get("base_object"),
                    description=cube.get("description") or props.get("description"),
                    measures=[
                        str(item["name"])
                        for item in cube.get("measures", []) or []
                        if isinstance(item, dict) and item.get("name")
                    ],
                    dimensions=[
                        str(item["name"])
                        for item in cube.get("dimensions", []) or []
                        if isinstance(item, dict) and item.get("name")
                    ],
                    time_dimensions=[
                        str(item["name"])
                        for item in cube.get("timeDimensions", []) or []
                        if isinstance(item, dict) and item.get("name")
                    ],
                )
            )
        return result

    @staticmethod
    def describe_cube(manifest: dict[str, Any], name: str) -> WrenCubeDetail:
        cube = next(
            (
                item
                for item in manifest.get("cubes", []) or []
                if isinstance(item, dict) and item.get("name") == name
            ),
            None,
        )
        if cube is None:
            raise WrenOperationError(
                "cube_not_found",
                "metadata_fetching",
                f"cube '{name}' was not found in the active MDL",
            )
        normalized = {
            "name": cube.get("name"),
            "base_object": cube.get("baseObject") or cube.get("base_object"),
            "measures": cube.get("measures") or [],
            "dimensions": cube.get("dimensions") or [],
            "time_dimensions": cube.get("timeDimensions") or [],
            "hierarchies": cube.get("hierarchies") or {},
            "properties": cube.get("properties") or {},
        }
        return WrenCubeDetail.model_validate(normalized)

    @staticmethod
    def to_sql(manifest: dict[str, Any], query: WrenCubeQuery) -> str:
        try:
            from wren_core import cube_query_to_sql

            payload = query.model_dump(
                by_alias=True,
                exclude_defaults=True,
                exclude_none=True,
            )
            return cube_query_to_sql(
                json.dumps(payload, ensure_ascii=False),
                json.dumps(manifest, ensure_ascii=False),
            )
        except WrenOperationError:
            raise
        except Exception as exc:
            raise WrenOperationError(
                "cube_query_invalid",
                "sql_planning",
                _safe_error(exc),
            ) from exc


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip().replace("\n", " ")
    return text[:500] or type(exc).__name__


def _connection_info(database_url: str, statement_timeout_ms: int) -> dict[str, Any]:
    bounded_timeout = max(100, min(statement_timeout_ms, 60_000))
    return {
        "connectionUrl": database_url,
        "kwargs": {
            "connect_timeout": "5",
            "options": f"-c statement_timeout={bounded_timeout}ms",
        },
    }


__all__ = [
    "WrenCubeDetail",
    "WrenCubeFilter",
    "WrenCubeOrderBy",
    "WrenCubeQuery",
    "WrenCubeQueryResponse",
    "WrenCubeService",
    "WrenCubeSummary",
    "WrenCubeTimeDimension",
    "WrenDryRunResponse",
    "WrenNativeRuntime",
    "WrenOperationError",
    "WrenPlanResponse",
]

"""Bounded PostgreSQL execution under an explicit read-only transaction."""

from __future__ import annotations

import os
from time import perf_counter

import psycopg
from psycopg.rows import dict_row

from packages.domain import QueryExecutionResult


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class ExecutionSettings:
    def __init__(
        self,
        *,
        enabled: bool,
        database_url: str,
        statement_timeout_ms: int,
        max_rows: int,
    ) -> None:
        self.enabled = enabled
        self.database_url = database_url
        self.statement_timeout_ms = max(100, min(statement_timeout_ms, 60_000))
        self.max_rows = max(1, min(max_rows, 10_000))

    @classmethod
    def from_env(cls) -> ExecutionSettings:
        enabled = os.getenv("ANALYTICS_EXECUTION_ENABLED", "false").lower() == "true"
        return cls(
            enabled=enabled,
            database_url=os.getenv("ANALYTICS_DATABASE_URL", "").strip(),
            statement_timeout_ms=_int_env("ANALYTICS_DATABASE_STATEMENT_TIMEOUT_MS", 15_000),
            max_rows=_int_env("ANALYTICS_DATABASE_MAX_ROWS", 1_000),
        )

    @property
    def configured(self) -> bool:
        placeholders = ("CHANGE_ME", "PROJECT_REF", "POOLER_HOST", "YOUR_")
        return bool(self.database_url) and not any(
            marker in self.database_url for marker in placeholders
        )


class DatabaseExecutionError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(f"read-only database execution failed ({code})")
        self.code = code


class PostgreSQLReadOnlyExecutor:
    def __init__(self, settings: ExecutionSettings) -> None:
        self._settings = settings

    def execute_sql(
        self,
        sql: str,
        parameters: dict[str, object] | None = None,
    ) -> QueryExecutionResult:
        if not self._settings.enabled:
            raise DatabaseExecutionError("execution_disabled")
        if not self._settings.configured:
            raise DatabaseExecutionError("database_not_configured")

        started = perf_counter()
        try:
            with psycopg.connect(
                self._settings.database_url,
                autocommit=True,
                connect_timeout=5,
                row_factory=dict_row,
            ) as connection:
                connection.execute("BEGIN TRANSACTION READ ONLY")
                try:
                    connection.execute(
                        "SELECT set_config('statement_timeout', %s, true)",
                        (f"{self._settings.statement_timeout_ms}ms",),
                    )
                    read_only = connection.execute(
                        "SHOW transaction_read_only"
                    ).fetchone()
                    if read_only is None or read_only["transaction_read_only"] != "on":
                        raise DatabaseExecutionError("read_only_not_enforced")
                    with connection.cursor() as cursor:
                        cursor.execute(sql, parameters or {})
                        fetched = cursor.fetchmany(self._settings.max_rows + 1)
                        columns = [column.name for column in cursor.description or ()]
                finally:
                    connection.execute("ROLLBACK")
        except DatabaseExecutionError:
            raise
        except psycopg.OperationalError as exc:
            raise DatabaseExecutionError("database_unavailable") from exc
        except psycopg.Error as exc:
            raise DatabaseExecutionError("query_failed") from exc

        truncated = len(fetched) > self._settings.max_rows
        rows = fetched[: self._settings.max_rows]
        return QueryExecutionResult(
            columns=columns,
            rows=[dict(row) for row in rows],
            row_count=len(rows),
            truncated=truncated,
            duration_ms=max(0, round((perf_counter() - started) * 1000)),
        )

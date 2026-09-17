"""Fail-closed SQL policy for logical and expanded Wren SQL."""

from __future__ import annotations

from typing import Any, ClassVar, Literal

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from packages.domain import SQLSecurityReport, ValidationDecision


class WrenSQLSecurityValidator:
    """Validate the SQL proposal before and after Wren planning.

    Logical SQL may reference only Wren model names. Expanded SQL may reference
    only the physical schema-qualified relations declared by those models.
    Both stages must remain a single read-only SELECT with a bounded LIMIT.
    """

    _FORBIDDEN_FUNCTIONS: ClassVar[set[str]] = {
        "dblink",
        "dblink_exec",
        "lo_export",
        "lo_import",
        "pg_read_binary_file",
        "pg_read_file",
        "pg_sleep",
        "pg_terminate_backend",
        "set_config",
    }

    def __init__(self, *, max_rows: int = 1_000) -> None:
        self._max_rows = max_rows

    def inspect(
        self,
        sql: str,
        manifest: dict[str, Any],
        *,
        stage: Literal["logical", "expanded"],
    ) -> SQLSecurityReport:
        checks: list[str] = []
        try:
            statements = sqlglot.parse(sql, read="postgres")
        except ParseError:
            return self._reject("parse_error", checks=checks)
        if len(statements) != 1:
            return self._reject("multiple_statements", checks=checks)

        statement = statements[0]
        statement_type = type(statement).__name__
        if not isinstance(statement, exp.Select):
            return self._reject(
                "non_select_statement",
                statement_type=statement_type,
                checks=checks,
            )
        checks.append("single_select_statement")

        if statement.find(exp.Lock) is not None:
            return self._reject(
                "locking_clause_forbidden",
                statement_type=statement_type,
                checks=checks,
            )
        checks.append("no_locking_clause")

        for function in statement.find_all(exp.Func):
            if function.sql_name().lower() in self._FORBIDDEN_FUNCTIONS:
                return self._reject(
                    "unsafe_function",
                    statement_type=statement_type,
                    checks=checks,
                )
        checks.append("no_unsafe_function")

        if stage == "logical":
            allowed = _logical_relations(manifest)
        else:
            allowed = _physical_relations(manifest)
        cte_names = {
            cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE)
        }
        relations: set[str] = set()
        for table in statement.find_all(exp.Table):
            name = table.name.lower()
            # A planned Wren CTE commonly reuses the logical model name while
            # its body contains the schema-qualified physical relation with the
            # same basename.  Skip only the unqualified CTE reference; never
            # skip the physical table or the allowlist would be bypassed and
            # the report would lose its evidence.
            if not name or (
                name in cte_names and not (table.catalog or table.db)
            ):
                continue
            if stage == "logical":
                if table.catalog or table.db:
                    return self._reject(
                        "logical_relation_must_use_wren_model",
                        statement_type=statement_type,
                        relations=relations,
                        checks=checks,
                    )
                relation = name
            else:
                if table.catalog or not table.db:
                    return self._reject(
                        "expanded_relation_must_be_schema_qualified",
                        statement_type=statement_type,
                        relations=relations,
                        checks=checks,
                    )
                relation = f"{table.db}.{table.name}".lower()
            relations.add(relation)
            if relation not in allowed:
                return self._reject(
                    "relation_not_allowed",
                    statement_type=statement_type,
                    relations=relations,
                    checks=checks,
                )
        if not relations and not cte_names:
            return self._reject(
                "missing_governed_relation",
                statement_type=statement_type,
                checks=checks,
            )
        checks.append(f"{stage}_relations_allowlisted")

        limit = statement.args.get("limit")
        if limit is None:
            return self._reject(
                "row_limit_required",
                statement_type=statement_type,
                relations=relations,
                checks=checks,
            )
        limit_value = _literal_limit(limit.expression)
        if limit_value is None or not 1 <= limit_value <= self._max_rows:
            return self._reject(
                "row_limit_invalid",
                statement_type=statement_type,
                relations=relations,
                checks=checks,
            )
        checks.append("row_limit_enforced")

        return SQLSecurityReport(
            decision=ValidationDecision.PASS,
            statement_type=statement_type,
            referenced_relations=sorted(relations),
            checks=checks,
        )

    @staticmethod
    def _reject(
        code: str,
        *,
        statement_type: str | None = None,
        relations: set[str] | None = None,
        checks: list[str],
    ) -> SQLSecurityReport:
        return SQLSecurityReport(
            decision=ValidationDecision.REJECT,
            statement_type=statement_type,
            referenced_relations=sorted(relations or set()),
            checks=checks,
            error_code=code,
        )


def _logical_relations(manifest: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in ("models", "views", "cubes"):
        for item in manifest.get(key, []) or []:
            if isinstance(item, dict) and item.get("name"):
                names.add(str(item["name"]).lower())
    return names


def _physical_relations(manifest: dict[str, Any]) -> set[str]:
    relations: set[str] = set()
    for model in manifest.get("models", []) or []:
        if not isinstance(model, dict):
            continue
        reference = model.get("tableReference") or model.get("table_reference")
        if not isinstance(reference, dict):
            continue
        schema = reference.get("schema")
        table = reference.get("table")
        if schema and table:
            relations.add(f"{schema}.{table}".lower())
    return relations


def _literal_limit(expression: exp.Expression) -> int | None:
    if not isinstance(expression, exp.Literal) or expression.is_string:
        return None
    try:
        return int(expression.this)
    except (TypeError, ValueError):
        return None

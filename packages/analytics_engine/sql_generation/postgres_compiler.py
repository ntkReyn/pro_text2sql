"""Deterministically compile governed semantic plans to parameterized PostgreSQL."""

from __future__ import annotations

from packages.analytics_engine.validation import SemanticPlanValidator
from packages.domain.query_contracts import (
    FilterOperator,
    QueryFilter,
    SQLCandidate,
    SemanticQueryPlan,
)
from packages.semantic_layer.catalog import SemanticCatalog


_OPERATOR_SQL = {
    FilterOperator.EQ: "=",
    FilterOperator.NE: "<>",
    FilterOperator.GT: ">",
    FilterOperator.GTE: ">=",
    FilterOperator.LT: "<",
    FilterOperator.LTE: "<=",
}


def _quote_identifier(identifier: str) -> str:
    # Identifiers have already passed the strict domain regex.
    return f'"{identifier}"'


class PostgreSQLSemanticCompiler:
    def __init__(self, catalog: SemanticCatalog) -> None:
        self._catalog = catalog
        self._validator = SemanticPlanValidator(catalog)

    def compile(
        self,
        plan: SemanticQueryPlan,
        *,
        allow_draft_metrics: bool = False,
    ) -> SQLCandidate:
        metric = self._validator.validate(
            plan,
            allow_draft_metrics=allow_draft_metrics,
        )

        select_parts: list[str] = []
        group_parts: list[str] = []
        for dimension_id in plan.dimensions:
            dimension = self._catalog.dimension(dimension_id)
            select_parts.append(
                f"{dimension.expression} AS {_quote_identifier(dimension.id)}"
            )
            group_parts.append(dimension.expression)
        select_parts.append(f"{metric.expression} AS {_quote_identifier(metric.id)}")

        where_parts = list(metric.base_filters)
        parameters: dict[str, object] = {}
        if plan.time_range is not None and metric.time_dimension is not None:
            where_parts.extend(
                [
                    f"{metric.time_dimension} >= %(time_start)s",
                    f"{metric.time_dimension} < %(time_end)s",
                ]
            )
            parameters["time_start"] = plan.time_range.start
            parameters["time_end"] = plan.time_range.end_exclusive

        for index, query_filter in enumerate(plan.filters):
            dimension = self._catalog.dimension(query_filter.field)
            filter_sql, filter_parameters = self._compile_filter(
                index,
                dimension.expression,
                query_filter,
            )
            where_parts.append(filter_sql)
            parameters.update(filter_parameters)

        sql_lines = [
            "SELECT",
            "  " + ",\n  ".join(select_parts),
            f"FROM {metric.base_relation}",
        ]
        if where_parts:
            sql_lines.extend(["WHERE", "  " + "\n  AND ".join(where_parts)])
        if group_parts:
            sql_lines.extend(["GROUP BY", "  " + ",\n  ".join(group_parts)])
        if plan.sort:
            sort_parts = [
                f"{_quote_identifier(item.field)} {item.direction.value.upper()}"
                for item in plan.sort
            ]
            sql_lines.append("ORDER BY " + ", ".join(sort_parts))
        sql_lines.append("LIMIT %(row_limit)s")
        parameters["row_limit"] = plan.limit

        return SQLCandidate(
            sql="\n".join(sql_lines),
            parameters=parameters,
            metric_id=metric.id,
            metric_version=metric.version,
            plan_version=plan.plan_version,
        )

    @staticmethod
    def _compile_filter(
        index: int,
        field_expression: str,
        query_filter: QueryFilter,
    ) -> tuple[str, dict[str, object]]:
        if query_filter.operator is FilterOperator.IN:
            assert isinstance(query_filter.value, list)
            names = [f"filter_{index}_{item_index}" for item_index in range(len(query_filter.value))]
            placeholders = ", ".join(f"%({name})s" for name in names)
            return (
                f"{field_expression} IN ({placeholders})",
                dict(zip(names, query_filter.value, strict=True)),
            )

        assert not isinstance(query_filter.value, list)
        parameter_name = f"filter_{index}"
        operator = _OPERATOR_SQL[query_filter.operator]
        return (
            f"{field_expression} {operator} %({parameter_name})s",
            {parameter_name: query_filter.value},
        )

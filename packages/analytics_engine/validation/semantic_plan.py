"""Cross-check a query plan against the governed semantic catalog."""

from __future__ import annotations

from packages.domain.query_contracts import SemanticQueryPlan
from packages.semantic_layer.catalog import SemanticCatalog
from packages.semantic_layer.models import CatalogStatus, MetricDefinition


class SemanticPlanValidationError(ValueError):
    """A plan violates a metric, dimension, or governance contract."""


class SemanticPlanValidator:
    def __init__(self, catalog: SemanticCatalog) -> None:
        self._catalog = catalog

    def validate(
        self,
        plan: SemanticQueryPlan,
        *,
        allow_draft_metrics: bool = False,
    ) -> MetricDefinition:
        try:
            metric = self._catalog.metric(plan.metric_id, plan.metric_version)
        except ValueError as exc:
            raise SemanticPlanValidationError(str(exc)) from exc

        if metric.status is CatalogStatus.DEPRECATED:
            raise SemanticPlanValidationError(
                f"metric {metric.id}@{metric.version} is deprecated"
            )
        if metric.status is CatalogStatus.DRAFT and not allow_draft_metrics:
            raise SemanticPlanValidationError(
                f"metric {metric.id}@{metric.version} is draft and cannot be compiled"
            )

        invalid_dimensions = set(plan.dimensions) - set(metric.allowed_dimensions)
        if invalid_dimensions:
            raise SemanticPlanValidationError(
                f"dimensions not allowed for {metric.id}: "
                f"{', '.join(sorted(invalid_dimensions))}"
            )

        if metric.time_dimension and plan.time_range is None:
            raise SemanticPlanValidationError(
                f"metric {metric.id} requires an explicit time range"
            )

        for query_filter in plan.filters:
            if query_filter.field not in metric.allowed_filter_fields:
                raise SemanticPlanValidationError(
                    f"filter field not allowed for {metric.id}: {query_filter.field}"
                )
            dimension = self._catalog.dimension(query_filter.field)
            if query_filter.operator not in dimension.allowed_operators:
                raise SemanticPlanValidationError(
                    f"operator {query_filter.operator} is not allowed for "
                    f"{query_filter.field}"
                )

        selected_output_fields = set(plan.dimensions) | {metric.id}
        invalid_sort_fields = {
            item.field for item in plan.sort if item.field not in selected_output_fields
        }
        if invalid_sort_fields:
            raise SemanticPlanValidationError(
                "sort fields must be selected dimensions or the metric: "
                f"{', '.join(sorted(invalid_sort_fields))}"
            )

        return metric

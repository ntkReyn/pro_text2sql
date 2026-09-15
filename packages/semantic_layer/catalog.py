"""Loader and resolver for repository-owned semantic metadata."""

from __future__ import annotations

import json
from pathlib import Path

from packages.semantic_layer.models import DimensionDefinition, MetricDefinition


class CatalogError(ValueError):
    """Raised when semantic metadata is missing, duplicated, or inconsistent."""


class SemanticCatalog:
    def __init__(
        self,
        metrics: list[MetricDefinition],
        dimensions: list[DimensionDefinition],
    ) -> None:
        self._metrics = self._index_metrics(metrics)
        self._dimensions = self._index_dimensions(dimensions)
        self._validate_references()

    @staticmethod
    def _index_metrics(
        metrics: list[MetricDefinition],
    ) -> dict[tuple[str, str], MetricDefinition]:
        indexed: dict[tuple[str, str], MetricDefinition] = {}
        for metric in metrics:
            key = (metric.id, metric.version)
            if key in indexed:
                raise CatalogError(f"duplicate metric version: {metric.id}@{metric.version}")
            indexed[key] = metric
        return indexed

    @staticmethod
    def _index_dimensions(
        dimensions: list[DimensionDefinition],
    ) -> dict[str, DimensionDefinition]:
        indexed: dict[str, DimensionDefinition] = {}
        for dimension in dimensions:
            if dimension.id in indexed:
                raise CatalogError(f"duplicate dimension: {dimension.id}")
            indexed[dimension.id] = dimension
        return indexed

    def _validate_references(self) -> None:
        known = set(self._dimensions)
        for metric in self._metrics.values():
            missing = (set(metric.allowed_dimensions) | set(metric.allowed_filter_fields)) - known
            if missing:
                raise CatalogError(
                    f"metric {metric.id}@{metric.version} references unknown dimensions: "
                    f"{', '.join(sorted(missing))}"
                )

    @classmethod
    def from_files(cls, metrics_path: Path, dimensions_path: Path) -> "SemanticCatalog":
        metrics_payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        dimensions_payload = json.loads(dimensions_path.read_text(encoding="utf-8"))
        return cls(
            metrics=[MetricDefinition.model_validate(item) for item in metrics_payload["metrics"]],
            dimensions=[
                DimensionDefinition.model_validate(item)
                for item in dimensions_payload["dimensions"]
            ],
        )

    def metric(self, metric_id: str, version: str) -> MetricDefinition:
        try:
            return self._metrics[(metric_id, version)]
        except KeyError as exc:
            raise CatalogError(f"unknown metric version: {metric_id}@{version}") from exc

    def dimension(self, dimension_id: str) -> DimensionDefinition:
        try:
            return self._dimensions[dimension_id]
        except KeyError as exc:
            raise CatalogError(f"unknown dimension: {dimension_id}") from exc

    @property
    def metrics(self) -> tuple[MetricDefinition, ...]:
        return tuple(self._metrics.values())

    @property
    def dimensions(self) -> tuple[DimensionDefinition, ...]:
        return tuple(self._dimensions.values())


def load_default_catalog() -> SemanticCatalog:
    root = Path(__file__).resolve().parent
    return SemanticCatalog.from_files(
        root / "metrics" / "supplier_delivery_metrics.v1.json",
        root / "dimensions" / "supplier_delivery_dimensions.v1.json",
    )

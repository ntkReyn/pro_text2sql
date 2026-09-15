"""Governed, non-PII value grounding for semantic filters."""

from __future__ import annotations

import json
import re
from pathlib import Path

from packages.domain import GroundedValue
from packages.semantic_layer.catalog import CatalogError, SemanticCatalog
from packages.semantic_layer.models import GovernedValueDefinition
from packages.shared.text import normalize_vietnamese


class GovernedValueIndex:
    def __init__(
        self,
        *,
        version: str,
        values: list[GovernedValueDefinition],
        catalog: SemanticCatalog,
    ) -> None:
        self.version = version
        self._values = tuple(values)
        for value in values:
            catalog.dimension(value.field)
            if value.classification not in {"public", "internal"}:
                raise CatalogError(
                    f"value index cannot contain restricted field values: {value.field}"
                )

    @classmethod
    def from_file(cls, path: Path, catalog: SemanticCatalog) -> "GovernedValueIndex":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            version=payload["catalog_version"],
            values=[
                GovernedValueDefinition.model_validate(item)
                for item in payload["values"]
            ],
            catalog=catalog,
        )

    def ground(self, normalized_question: str) -> list[GroundedValue]:
        matches: list[GroundedValue] = []
        claimed_fields: set[str] = set()
        candidates: list[tuple[int, GovernedValueDefinition, str]] = []
        for value in self._values:
            for alias in value.aliases_vi:
                normalized_alias = normalize_vietnamese(alias)
                candidates.append((len(normalized_alias), value, normalized_alias))

        for _, value, alias in sorted(candidates, key=lambda item: item[0], reverse=True):
            if value.field in claimed_fields:
                continue
            if re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", normalized_question):
                matches.append(
                    GroundedValue(
                        field=value.field,
                        canonical_value=value.canonical_value,
                        matched_alias=alias,
                        source_version=self.version,
                        confidence=1.0,
                    )
                )
                claimed_fields.add(value.field)
        return matches


def load_default_value_index(catalog: SemanticCatalog) -> GovernedValueIndex:
    root = Path(__file__).resolve().parent
    return GovernedValueIndex.from_file(
        root / "values" / "ev_customer_values.vi.v1.json",
        catalog,
    )

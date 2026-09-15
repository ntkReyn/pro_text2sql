"""Deterministic B1 structure-aware retrieval over reviewed examples.

This is an inspectable baseline for Semantic-DAIL. It deliberately avoids an
embedding/LLM dependency so later adapters can be measured against it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from packages.domain import (
    GroundedValue,
    PreliminaryIntentSketch,
    RetrievedExample,
    SemanticQueryPlan,
)
from packages.semantic_layer import SemanticCatalog
from packages.shared.text import normalize_vietnamese


_STOP_WORDS = {
    "co", "cua", "la", "trong", "tai", "bao", "nhieu", "nhung", "cac",
    "cho", "va", "duoc", "the", "nao", "nam",
}


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", normalize_vietnamese(value))
        if token not in _STOP_WORDS
    }


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def _metric_family(metric_id: str) -> str:
    if "rate" in metric_id:
        return "rate"
    if metric_id.startswith("average_"):
        return "average"
    if "energy" in metric_id:
        return "sum"
    return "count"


def _plan_structure(plan: SemanticQueryPlan) -> set[str]:
    tokens = {
        f"aggregate:{_metric_family(plan.metric_id)}",
        f"group-count:{len(plan.dimensions)}",
        f"filter-count:{len(plan.filters)}",
        f"time:{'yes' if plan.time_range else 'no'}",
        f"limit:{'bounded' if plan.limit < 100 else 'default'}",
    }
    if plan.dimensions:
        tokens.add("group-by")
    return tokens


class PreliminaryIntentSketcher:
    def __init__(self, catalog: SemanticCatalog) -> None:
        self._catalog = catalog

    def sketch(
        self,
        canonical_question: str,
        grounded_values: list[GroundedValue],
    ) -> PreliminaryIntentSketch:
        operations: list[str] = []
        if "ty le" in canonical_question:
            operations.append("rate")
        elif "trung binh" in canonical_question:
            operations.append("average")
        elif "kwh" in canonical_question or "dien nang" in canonical_question:
            operations.append("sum")
        else:
            operations.append("count")
        if "theo " in canonical_question:
            operations.append("group-by")
        if "xu huong" in canonical_question or any(
            term in canonical_question for term in ("theo tuan", "theo thang")
        ):
            operations.append("trend")
        if "top" in canonical_question or "nhat" in canonical_question:
            operations.append("ranking")

        dimensions = self._dimension_candidates(canonical_question)
        metric_candidates = self._metric_candidates(canonical_question, operations)
        time_scope = bool(
            re.search(r"\b(thang|quy|nam)\s*[0-9]", canonical_question)
        )
        limit_match = re.search(r"\btop\s*(\d+)\b", canonical_question)
        requested_limit = min(int(limit_match.group(1)), 500) if limit_match else None
        filter_fields = list(dict.fromkeys(value.field for value in grounded_values))
        structure_tokens = {
            f"aggregate:{operations[0]}",
            f"group-count:{len(dimensions)}",
            f"filter-count:{len(filter_fields)}",
            f"time:{'yes' if time_scope else 'no'}",
            f"limit:{'bounded' if requested_limit or 'nhat' in canonical_question else 'default'}",
        }
        if dimensions:
            structure_tokens.add("group-by")

        return PreliminaryIntentSketch(
            metric_candidates=metric_candidates,
            dimension_candidates=dimensions,
            filter_fields=filter_fields,
            operations=operations,
            has_time_scope=time_scope,
            requested_limit=requested_limit,
            structure_tokens=sorted(structure_tokens),
        )

    def _dimension_candidates(self, question: str) -> list[str]:
        matched: list[str] = []
        for dimension in self._catalog.dimensions:
            aliases = [dimension.label, *dimension.aliases_vi]
            grouping_aliases: list[str] = []
            for alias in aliases:
                normalized_alias = normalize_vietnamese(alias)
                grouping_aliases.extend(
                    {
                        normalized_alias,
                        normalized_alias.replace(" khach hang", ""),
                        normalized_alias.replace(" sac", ""),
                        normalized_alias.replace(" dich vu", ""),
                    }
                )
            if any(
                alias
                and (
                    f"theo {alias}" in question
                    or f"{alias} nao" in question
                )
                for alias in grouping_aliases
            ):
                matched.append(dimension.id)
        return matched[:5]

    def _metric_candidates(self, question: str, operations: list[str]) -> list[str]:
        question_tokens = _tokens(question)
        scored: list[tuple[float, str]] = []
        for metric in self._catalog.metrics:
            searchable = f"{metric.label} {metric.description} {metric.id.replace('_', ' ')}"
            overlap = _jaccard(question_tokens, _tokens(searchable))
            family_bonus = 0.25 if _metric_family(metric.id) == operations[0] else 0.0
            score = min(overlap + family_bonus, 1.0)
            if score > 0:
                scored.append((score, metric.id))
        return [metric_id for _, metric_id in sorted(scored, reverse=True)[:5]]


class SemanticDAILSelector:
    def __init__(
        self,
        *,
        catalog: SemanticCatalog,
        examples_path: Path,
        sketcher: PreliminaryIntentSketcher,
    ) -> None:
        self._catalog = catalog
        self._sketcher = sketcher
        self._examples = [
            json.loads(line)
            for line in examples_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    @classmethod
    def default(
        cls,
        catalog: SemanticCatalog,
        sketcher: PreliminaryIntentSketcher,
    ) -> "SemanticDAILSelector":
        root = Path(__file__).resolve().parents[3]
        return cls(
            catalog=catalog,
            examples_path=root / "evals" / "datasets" / "ev_customer_v1.jsonl",
            sketcher=sketcher,
        )

    def select(
        self,
        canonical_question: str,
        sketch: PreliminaryIntentSketch,
        *,
        limit: int = 3,
    ) -> list[RetrievedExample]:
        query_tokens = _tokens(canonical_question)
        query_structure = set(sketch.structure_tokens)
        results: list[RetrievedExample] = []
        for item in self._examples:
            plan = SemanticQueryPlan.model_validate(item["expected_plan"])
            semantic_similarity = _jaccard(query_tokens, _tokens(item["question"]))
            structure_similarity = _jaccard(query_structure, _plan_structure(plan))
            metric_overlap = 1.0 if plan.metric_id in sketch.metric_candidates else 0.0
            dimension_overlap = _jaccard(
                set(sketch.dimension_candidates), set(plan.dimensions)
            )
            filter_overlap = _jaccard(
                set(sketch.filter_fields), {query_filter.field for query_filter in plan.filters}
            )
            governed_overlap = (metric_overlap + dimension_overlap + filter_overlap) / 3
            verified_quality = 1.0
            score = min(
                0.35 * semantic_similarity
                + 0.40 * structure_similarity
                + 0.15 * governed_overlap
                + 0.10 * verified_quality,
                1.0,
            )
            results.append(
                RetrievedExample(
                    case_id=item["case_id"],
                    question=item["question"],
                    metric_id=plan.metric_id,
                    semantic_similarity=round(semantic_similarity, 4),
                    structure_similarity=round(structure_similarity, 4),
                    governed_overlap=round(governed_overlap, 4),
                    verified_quality=verified_quality,
                    score=round(score, 4),
                )
            )
        return sorted(results, key=lambda item: (-item.score, item.case_id))[:limit]

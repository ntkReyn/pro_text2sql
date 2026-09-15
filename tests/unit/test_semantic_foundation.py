from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from packages.analytics_engine.sql_generation import PostgreSQLSemanticCompiler
from packages.analytics_engine.validation import SemanticPlanValidationError
from packages.domain import SemanticQueryPlan
from packages.semantic_layer import load_default_catalog


class SemanticFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()
        cls.compiler = PostgreSQLSemanticCompiler(cls.catalog)

    def test_default_catalog_loads_five_draft_metrics(self) -> None:
        self.assertEqual(len(self.catalog.metrics), 5)
        self.assertTrue(all(metric.status.value == "draft" for metric in self.catalog.metrics))
        self.assertEqual(len(self.catalog.dimensions), 5)

    def test_draft_metric_is_rejected_without_explicit_development_override(self) -> None:
        plan = self._ranking_plan()
        with self.assertRaisesRegex(SemanticPlanValidationError, "is draft"):
            self.compiler.compile(plan)

    def test_ranking_plan_compiles_to_parameterized_postgres(self) -> None:
        candidate = self.compiler.compile(
            self._ranking_plan(),
            allow_draft_metrics=True,
        )

        self.assertIn(
            '100.0 * COUNT(*) FILTER (WHERE is_late = TRUE) / NULLIF(COUNT(*), 0) AS "late_delivery_rate"',
            candidate.sql,
        )
        self.assertIn('supplier_name AS "supplier_name"', candidate.sql)
        self.assertIn("completed_at >= %(time_start)s", candidate.sql)
        self.assertIn('ORDER BY "late_delivery_rate" DESC', candidate.sql)
        self.assertNotIn("2026-07-01", candidate.sql)
        self.assertEqual(candidate.parameters["time_start"], date(2026, 7, 1))
        self.assertEqual(candidate.parameters["row_limit"], 5)

    def test_filter_value_cannot_become_sql(self) -> None:
        malicious_value = "Kho Ha Noi'; DROP TABLE analytics.dim_supplier; --"
        plan = SemanticQueryPlan.model_validate(
            {
                "metric_id": "completed_po_line_count",
                "metric_version": "1.0.0",
                "dimensions": [],
                "grain": [],
                "filters": [
                    {
                        "field": "warehouse_name",
                        "operator": "eq",
                        "value": malicious_value,
                    }
                ],
                "time_range": {
                    "start": "2026-07-01",
                    "end_exclusive": "2026-08-01",
                },
            }
        )

        candidate = self.compiler.compile(plan, allow_draft_metrics=True)

        self.assertNotIn(malicious_value, candidate.sql)
        self.assertEqual(candidate.parameters["filter_0"], malicious_value)

    def test_unknown_dimension_is_rejected(self) -> None:
        payload = self._ranking_plan().model_dump(mode="json")
        payload["dimensions"] = ["product_sku"]
        payload["grain"] = ["product_sku"]
        plan = SemanticQueryPlan.model_validate(payload)

        with self.assertRaisesRegex(SemanticPlanValidationError, "not allowed"):
            self.compiler.compile(plan, allow_draft_metrics=True)

    def test_time_range_is_required_by_supplier_delivery_metrics(self) -> None:
        payload = self._ranking_plan().model_dump(mode="json")
        payload["time_range"] = None
        plan = SemanticQueryPlan.model_validate(payload)

        with self.assertRaisesRegex(SemanticPlanValidationError, "explicit time range"):
            self.compiler.compile(plan, allow_draft_metrics=True)

    def test_grain_must_equal_selected_dimensions(self) -> None:
        payload = self._ranking_plan().model_dump(mode="json")
        payload["grain"] = []
        with self.assertRaisesRegex(ValidationError, "output grain"):
            SemanticQueryPlan.model_validate(payload)

    def test_every_initial_eval_case_has_a_valid_compilable_plan(self) -> None:
        dataset = (
            Path(__file__).parents[2]
            / "evals"
            / "datasets"
            / "supplier_delivery_v1.jsonl"
        )
        cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                plan = SemanticQueryPlan.model_validate(case["expected_plan"])
                candidate = self.compiler.compile(plan, allow_draft_metrics=True)
                self.assertEqual(candidate.metric_id, plan.metric_id)

    @staticmethod
    def _ranking_plan() -> SemanticQueryPlan:
        return SemanticQueryPlan.model_validate(
            {
                "metric_id": "late_delivery_rate",
                "metric_version": "1.0.0",
                "dimensions": ["supplier_name"],
                "grain": ["supplier_name"],
                "time_range": {
                    "start": "2026-07-01",
                    "end_exclusive": "2026-10-01",
                },
                "sort": [{"field": "late_delivery_rate", "direction": "desc"}],
                "limit": 5,
            }
        )


if __name__ == "__main__":
    unittest.main()

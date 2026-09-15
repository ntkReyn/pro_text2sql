from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from packages.analytics_engine.planning import (
    ArchitectureBaselinePipeline,
    BaselinePlanner,
    PlanningStatus,
)
from packages.analytics_engine.sql_generation import PostgreSQLSemanticCompiler
from packages.analytics_engine.validation import SemanticPlanValidationError
from packages.domain import SemanticQueryPlan
from packages.semantic_layer import load_default_catalog


class SemanticFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_default_catalog()
        cls.compiler = PostgreSQLSemanticCompiler(cls.catalog)
        cls.planner = BaselinePlanner(cls.catalog)
        cls.architecture_pipeline = ArchitectureBaselinePipeline(cls.catalog)

    def test_default_catalog_loads_ev_charging_metrics(self) -> None:
        self.assertEqual(len(self.catalog.metrics), 13)
        self.assertTrue(all(metric.status.value == "draft" for metric in self.catalog.metrics))
        self.assertEqual(len(self.catalog.dimensions), 19)

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
            "100.0 * COUNT(*) FILTER (WHERE session_status = 'completed' AND energy_delivered_kwh > 0) / NULLIF(COUNT(*), 0) AS \"charging_success_rate\"",
            candidate.sql,
        )
        self.assertIn('station_region_code AS "station_region_code"', candidate.sql)
        self.assertIn("started_at >= %(time_start)s", candidate.sql)
        self.assertIn('ORDER BY "charging_success_rate" DESC', candidate.sql)
        self.assertNotIn("2026-07-01", candidate.sql)
        self.assertEqual(candidate.parameters["time_start"], date(2026, 7, 1))
        self.assertEqual(candidate.parameters["row_limit"], 5)

    def test_filter_value_cannot_become_sql(self) -> None:
        malicious_value = "Ha Noi'; DROP TABLE analytics.dim_vehicle; --"
        plan = SemanticQueryPlan.model_validate(
            {
                "metric_id": "successful_charging_session_count",
                "metric_version": "1.0.0",
                "dimensions": [],
                "grain": [],
                "filters": [
                    {
                        "field": "province_name",
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
        payload["dimensions"] = ["customer_email"]
        payload["grain"] = ["customer_email"]
        plan = SemanticQueryPlan.model_validate(payload)

        with self.assertRaisesRegex(SemanticPlanValidationError, "not allowed"):
            self.compiler.compile(plan, allow_draft_metrics=True)

    def test_time_range_is_required_by_ev_charging_metrics(self) -> None:
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
            / "ev_customer_v1.jsonl"
        )
        cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(cases), 16)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                plan = SemanticQueryPlan.model_validate(case["expected_plan"])
                candidate = self.compiler.compile(plan, allow_draft_metrics=True)
                self.assertEqual(candidate.metric_id, plan.metric_id)

    def test_baseline_reproduces_every_week1_expected_plan(self) -> None:
        dataset = Path(__file__).parents[2] / "evals" / "datasets" / "ev_customer_v1.jsonl"
        cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]

        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                result = self.planner.plan(case["question"])
                self.assertEqual(result.status, PlanningStatus.PLANNED, result.message)
                self.assertIsNotNone(result.plan)
                self.assertEqual(
                    result.plan.model_dump(mode="json"),
                    case["expected_plan"],
                )

    def test_baseline_asks_for_required_time_range(self) -> None:
        result = self.planner.plan("Có bao nhiêu phiên sạc thất bại?")

        self.assertEqual(result.status, PlanningStatus.NEEDS_CLARIFICATION)
        self.assertIsNone(result.plan)

    def test_baseline_abstains_from_unknown_metric(self) -> None:
        result = self.planner.plan("Hãy dự báo xe nào sẽ hỏng pin vào tuần tới")

        self.assertEqual(result.status, PlanningStatus.UNANSWERABLE)
        self.assertIsNone(result.plan)

    def test_b1_pipeline_expands_colloquial_customer_alias(self) -> None:
        result = self.architecture_pipeline.plan("Có bao nhiêu khách?")

        self.assertEqual(result.status, PlanningStatus.PLANNED)
        self.assertIsNotNone(result.plan)
        self.assertEqual(result.plan.metric_id, "customer_count")
        self.assertEqual(result.normalized_question, "co bao nhieu khach?")
        self.assertIsNotNone(result.trace)
        self.assertEqual(result.trace.canonical_question, "co bao nhieu khach hang?")

        canonical_result = self.architecture_pipeline.plan("Có bao nhiêu khách hàng?")
        self.assertEqual(canonical_result.status, PlanningStatus.PLANNED)
        self.assertEqual(canonical_result.trace.canonical_question, "co bao nhieu khach hang?")

    def test_b1_pipeline_grounds_alias_and_retrieves_structural_example(self) -> None:
        result = self.architecture_pipeline.plan(
            "Có bao nhiêu phiên sạc thành công tại HN trong tháng 8 năm 2026?"
        )

        self.assertEqual(result.status, PlanningStatus.PLANNED)
        self.assertIsNotNone(result.plan)
        self.assertEqual(result.plan.filters[0].field, "province_name")
        self.assertEqual(result.plan.filters[0].value, "Ha Noi")
        self.assertIsNotNone(result.trace)
        self.assertEqual(result.trace.plan_validation, "passed")
        self.assertEqual(result.trace.preliminary_intent.dimension_candidates, [])
        self.assertEqual(result.trace.retrieved_examples[0].case_id, "EV-006")

    def test_b1_pipeline_clarifies_ambiguous_business_term_before_retrieval(self) -> None:
        result = self.architecture_pipeline.plan(
            "Hiệu quả sạc trong quý 3 năm 2026 thế nào?"
        )

        self.assertEqual(result.status, PlanningStatus.NEEDS_CLARIFICATION)
        self.assertIsNone(result.plan)
        self.assertIsNotNone(result.trace)
        self.assertEqual(result.trace.gate_decision.value, "clarify")
        self.assertEqual(result.trace.retrieved_examples, [])

    def test_semantic_dail_prefers_matching_ranking_structure(self) -> None:
        result = self.architecture_pipeline.plan(
            "Top 3 dòng xe có nhiều phiên sạc thất bại nhất trong quý 3 năm 2026"
        )

        self.assertEqual(result.status, PlanningStatus.PLANNED)
        self.assertIsNotNone(result.trace)
        self.assertEqual(result.trace.retrieved_examples[0].case_id, "EV-002")

    def test_b1_pipeline_preserves_week1_plans_and_retrieves_exact_examples(self) -> None:
        dataset = Path(__file__).parents[2] / "evals" / "datasets" / "ev_customer_v1.jsonl"
        cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]

        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                result = self.architecture_pipeline.plan(case["question"])
                self.assertIsNotNone(result.plan)
                self.assertEqual(result.plan.model_dump(mode="json"), case["expected_plan"])
                self.assertIsNotNone(result.trace)
                self.assertEqual(
                    result.trace.retrieved_examples[0].case_id,
                    case["case_id"],
                )

    @staticmethod
    def _ranking_plan() -> SemanticQueryPlan:
        return SemanticQueryPlan.model_validate(
            {
                "metric_id": "charging_success_rate",
                "metric_version": "1.0.0",
                "dimensions": ["station_region_code"],
                "grain": ["station_region_code"],
                "time_range": {
                    "start": "2026-07-01",
                    "end_exclusive": "2026-10-01",
                },
                "sort": [{"field": "charging_success_rate", "direction": "desc"}],
                "limit": 5,
            }
        )


if __name__ == "__main__":
    unittest.main()

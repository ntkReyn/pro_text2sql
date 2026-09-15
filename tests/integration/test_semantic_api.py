from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from apps.api.main import app


class SemanticAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_catalog_lists_governed_metrics(self) -> None:
        response = self.client.get("/api/v1/catalog/metrics")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 13)
        self.assertEqual(payload[0]["status"], "draft")
        self.assertNotIn("expression", payload[0])

    def test_compile_endpoint_returns_sql_without_executing_it(self) -> None:
        response = self.client.post(
            "/api/v1/query/compile",
            json={
                "metric_id": "charging_success_rate",
                "metric_version": "1.0.0",
                "dimensions": ["station_region_code"],
                "grain": ["station_region_code"],
                "time_range": {
                    "start": "2026-07-01",
                    "end_exclusive": "2026-10-01",
                },
                "sort": [
                    {"field": "charging_success_rate", "direction": "desc"}
                ],
                "limit": 5,
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["dialect"], "postgres")
        self.assertIn("%(time_start)s", payload["sql"])
        self.assertNotIn("2026-07-01", payload["sql"])

    def test_compile_endpoint_rejects_missing_required_time_range(self) -> None:
        response = self.client.post(
            "/api/v1/query/compile",
            json={
                "metric_id": "charging_success_rate",
                "metric_version": "1.0.0",
                "dimensions": [],
                "grain": [],
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("explicit time range", response.json()["detail"])

    def test_baseline_endpoint_returns_typed_plan_without_calling_llm(self) -> None:
        response = self.client.post(
            "/api/v1/query/plan-baseline",
            json={"question": "Có bao nhiêu xe theo dòng xe?"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "planned")
        self.assertEqual(payload["plan"]["metric_id"], "vehicle_count")
        self.assertEqual(payload["plan"]["dimensions"], ["vehicle_model_code"])

    def test_baseline_query_endpoint_returns_plan_and_parameterized_sql(self) -> None:
        response = self.client.post(
            "/api/v1/query/baseline",
            json={
                "question": "Có bao nhiêu phiên sạc thành công tại Hà Nội trong tháng 8 năm 2026?"
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["planning"]["status"], "planned")
        self.assertEqual(
            payload["planning"]["plan"]["metric_id"],
            "successful_charging_session_count",
        )
        self.assertIn("%(filter_0)s", payload["candidate"]["sql"])
        self.assertEqual(payload["candidate"]["parameters"]["filter_0"], "Ha Noi")
        trace = payload["planning"]["trace"]
        self.assertEqual(trace["architecture_version"], "b1.0")
        self.assertEqual(trace["plan_validation"], "passed")
        self.assertEqual(trace["retrieved_examples"][0]["case_id"], "EV-006")

    def test_baseline_query_endpoint_does_not_compile_unanswerable_question(self) -> None:
        response = self.client.post(
            "/api/v1/query/baseline",
            json={"question": "Dự báo xe nào sẽ hỏng pin vào tuần tới"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["planning"]["status"], "unanswerable")
        self.assertIsNone(payload["candidate"])

    def test_baseline_query_accepts_colloquial_customer_alias(self) -> None:
        response = self.client.post(
            "/api/v1/query/baseline",
            json={"question": "Có bao nhiêu khách?"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["planning"]["status"], "planned")
        self.assertEqual(payload["planning"]["plan"]["metric_id"], "customer_count")
        self.assertEqual(
            payload["planning"]["trace"]["canonical_question"],
            "co bao nhieu khach hang?",
        )
        self.assertIn(
            'COUNT(*) AS "customer_count"',
            payload["candidate"]["sql"],
        )


if __name__ == "__main__":
    unittest.main()

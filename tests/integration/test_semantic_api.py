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
        self.assertEqual(len(payload), 5)
        self.assertEqual(payload[0]["status"], "draft")
        self.assertNotIn("expression", payload[0])

    def test_compile_endpoint_returns_sql_without_executing_it(self) -> None:
        response = self.client.post(
            "/api/v1/query/compile",
            json={
                "metric_id": "late_delivery_rate",
                "metric_version": "1.0.0",
                "dimensions": ["supplier_name"],
                "grain": ["supplier_name"],
                "time_range": {
                    "start": "2026-07-01",
                    "end_exclusive": "2026-10-01",
                },
                "sort": [
                    {"field": "late_delivery_rate", "direction": "desc"}
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
                "metric_id": "late_delivery_rate",
                "metric_version": "1.0.0",
                "dimensions": [],
                "grain": [],
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("explicit time range", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes.semantic import create_semantic_router
from packages.analytics_engine.wren_workflow import (
    WrenContextSummary,
    WrenModelSummary,
    WrenQueryResponse,
    WrenWorkflowTrace,
)
from packages.integrations import WrenSettings


class _FakeWorkflow:
    async def run(self, question: str, *, execute: bool = False) -> WrenQueryResponse:
        return WrenQueryResponse(
            status="planned",
            question=question,
            sql="SELECT COUNT(*) AS customer_count FROM customer_analytics_v1 LIMIT 10",
            planned_sql="WITH customer_analytics_v1 AS (SELECT 1 FROM analytics.customer_analytics_v1) SELECT COUNT(*) AS customer_count FROM customer_analytics_v1 LIMIT 10",
            context=WrenContextSummary(
                project="ev_analytics",
                models=[WrenModelSummary(name="customer_analytics_v1")],
            ),
            trace=WrenWorkflowTrace(
                context_loaded=True,
                dry_plan_attempts=1,
                stages=["load_context", "propose_sql", "validate_sql", "dry_plan"],
            ),
        )


class SemanticAPITests(unittest.TestCase):
    def test_app_exposes_only_wren_query_routes(self) -> None:
        paths = set(app.openapi()["paths"])

        self.assertIn("/api/v1/query/wren", paths)
        self.assertIn("/api/v1/wren/models", paths)
        self.assertNotIn("/api/v1/query/baseline", paths)
        self.assertNotIn("/api/v1/query/agentic", paths)

    def test_wren_endpoint_returns_wren_workflow_result(self) -> None:
        test_app = FastAPI()
        test_app.include_router(
            create_semantic_router(
                "test",
                wren_settings=WrenSettings(
                    wren_project_path="wren/ev_analytics",
                ),
                workflow=_FakeWorkflow(),
            )
        )

        with TestClient(test_app) as client:
            response = client.post(
                "/api/v1/query/wren",
                json={"question": "Có bao nhiêu khách?"},
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["status"], "planned")
        self.assertEqual(payload["context"]["project"], "ev_analytics")
        self.assertIn("customer_analytics_v1", payload["sql"])

    def test_execution_is_fail_closed(self) -> None:
        test_app = FastAPI()
        test_app.include_router(
            create_semantic_router(
                "test",
                wren_settings=WrenSettings(
                    wren_project_path="wren/ev_analytics",
                    analytics_execution_enabled=False,
                ),
                workflow=_FakeWorkflow(),
            )
        )

        with TestClient(test_app) as client:
            response = client.post(
                "/api/v1/query/wren",
                json={"question": "Có bao nhiêu khách?", "execute": True},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "execution_disabled")


if __name__ == "__main__":
    unittest.main()

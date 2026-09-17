from __future__ import annotations

import unittest
from types import SimpleNamespace

from packages.analytics_engine.wren_workflow import (
    WrenFirstWorkflow,
    WrenProjectContext,
)
from packages.integrations import OpenAIWrenAgent, WrenAgentProposal, WrenSettings


class _FakeAgent:
    async def propose(self, *, question: str, context: str, feedback: str | None = None):
        return WrenAgentProposal(
            status="ready",
            sql="SELECT COUNT(*) AS customer_count FROM customer_analytics_v1 LIMIT 10",
        )


class _FakeWorkflow(WrenFirstWorkflow):
    def _dry_plan(self, context, sql: str) -> str:
        return (
            "WITH customer_analytics_v1 AS (SELECT 1 FROM "
            "analytics.customer_analytics_v1) SELECT COUNT(*) AS customer_count "
            "FROM customer_analytics_v1 LIMIT 10"
        )


class _FakeCompletions:
    def create(self, **kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"status":"ready","sql":"SELECT 1","message":null,"assumptions":[]}'
                    )
                )
            ]
        )


class _FakeOpenAI:
    chat = SimpleNamespace(completions=_FakeCompletions())


class WrenWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def test_project_context_reads_wren_mdl_and_knowledge(self) -> None:
        context = WrenProjectContext("wren/ev_analytics").load()

        self.assertEqual(context.summary.project, "ev_analytics")
        self.assertIn("charging_session_analytics_v1", [m.name for m in context.summary.models])
        self.assertIn("knowledge/rules/canonical_metrics.md", context.summary.knowledge_files)
        self.assertIn("WREN SCHEMA", context.prompt)

    async def test_workflow_uses_wren_dry_plan(self) -> None:
        settings = WrenSettings(wren_project_path="wren/ev_analytics")
        workflow = _FakeWorkflow(settings, agent=_FakeAgent())

        result = await workflow.run("Có bao nhiêu khách?")

        self.assertEqual(result.status, "planned")
        self.assertEqual(result.security.decision.value, "pass")
        self.assertIn("analytics.customer_analytics_v1", result.planned_sql)
        self.assertEqual(result.trace.stages[-1], "dry_plan")


class OpenAIWrenAgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_agent_parses_structured_sql_proposal(self) -> None:
        settings = WrenSettings(llm_api_key="test-key")
        agent = OpenAIWrenAgent(settings, client=_FakeOpenAI())

        result = await agent.propose(question="test", context="schema")

        self.assertEqual(result.status, "ready")
        self.assertEqual(result.sql, "SELECT 1")


if __name__ == "__main__":
    unittest.main()

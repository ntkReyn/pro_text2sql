from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from wren.context import build_json

from packages.analytics_engine.validation import WrenSQLSecurityValidator
from packages.analytics_engine.wren_memory import WrenMemoryService
from packages.analytics_engine.wren_runtime import (
    WrenCubeQuery,
    WrenCubeService,
    WrenNativeRuntime,
    WrenOperationError,
)
from packages.analytics_engine.wren_workflow import WrenProjectContext

PROJECT = Path("wren/ev_analytics")


class WrenSemanticRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = build_json(PROJECT)

    def test_manifest_contains_governed_cubes(self) -> None:
        cubes = WrenCubeService.list_cubes(self.manifest)

        self.assertEqual(len(cubes), 6)
        self.assertIn("charging_session_metrics", {cube.name for cube in cubes})
        self.assertIn(
            "charging_success_rate",
            next(cube for cube in cubes if cube.name == "charging_session_metrics").measures,
        )

    def test_all_cubes_translate_through_wren_core(self) -> None:
        requests = {
            "customer_metrics": (["customer_count"], ["customer_segment"]),
            "vehicle_metrics": (["vehicle_count"], ["vehicle_status"]),
            "battery_health_metrics": (
                ["average_latest_battery_soh_pct", "battery_watch_vehicle_count"],
                ["vehicle_model_code"],
            ),
            "charging_session_metrics": (
                ["successful_charging_session_count", "charging_success_rate"],
                ["station_region_code"],
            ),
            "service_visit_metrics": (
                ["completed_service_visit_count", "repeat_issue_service_visit_count"],
                ["visit_status"],
            ),
            "charging_station_metrics": (
                ["charging_station_count", "operational_charging_station_count"],
                ["province_name"],
            ),
        }
        for cube, (measures, dimensions) in requests.items():
            with self.subTest(cube=cube):
                sql = WrenCubeService.to_sql(
                    self.manifest,
                    WrenCubeQuery(
                        cube=cube,
                        measures=measures,
                        dimensions=dimensions,
                        limit=100,
                    ),
                )
                self.assertIn("GROUP BY", sql)
                self.assertIn("LIMIT 100", sql)

    def test_dry_plan_and_expanded_policy_keep_physical_evidence(self) -> None:
        sql = "SELECT COUNT(*) AS customer_count FROM customer_analytics_v1 LIMIT 1"
        planned = WrenNativeRuntime().dry_plan(self.manifest, sql)
        report = WrenSQLSecurityValidator().inspect(
            planned,
            self.manifest,
            stage="expanded",
        )

        self.assertEqual(report.decision.value, "pass")
        self.assertIn("analytics.customer_analytics_v1", report.referenced_relations)

    def test_memory_uses_wren_full_schema_and_grep_recall(self) -> None:
        memory = WrenMemoryService(PROJECT, backend="grep")
        context = memory.fetch(self.manifest, "battery health")
        recalls = memory.recall("charging success rate", limit=1)

        self.assertEqual(context["strategy"], "full")
        self.assertIn("Cube: charging_session_metrics", context["schema"])
        self.assertEqual(len(recalls), 1)
        self.assertIn("charging_success_rate", recalls[0]["sql_query"])

    def test_memory_search_fallback_works_for_large_schemas(self) -> None:
        memory = WrenMemoryService(PROJECT, backend="grep")
        context = memory.fetch(self.manifest, "battery health", threshold=1_000)

        self.assertEqual(context["strategy"], "search")
        self.assertTrue(context["results"])
        self.assertTrue(any("battery_health" in item["text"] for item in context["results"]))

    def test_memory_store_is_markdown_source_of_truth(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            memory = WrenMemoryService(project, backend="grep")
            result = memory.store(
                "How many test customers are there?",
                "SELECT COUNT(*) FROM customer_analytics_v1 LIMIT 1",
                datasource="postgres",
                tags=["test"],
            )

            self.assertTrue((project / result["path"]).is_file())
            self.assertEqual(
                memory.recall("test customers", limit=1)[0]["datasource"],
                "postgres",
            )

    def test_dry_run_fails_closed_without_database(self) -> None:
        with self.assertRaises(WrenOperationError) as raised:
            WrenNativeRuntime().dry_run(
                self.manifest,
                "SELECT COUNT(*) FROM customer_analytics_v1 LIMIT 1",
                database_url="",
            )

        self.assertEqual(raised.exception.code, "database_not_configured")
        self.assertEqual(raised.exception.phase, "sql_dry_run")

    def test_question_context_recalls_relevant_pairs(self) -> None:
        snapshot = WrenProjectContext(PROJECT).load("charging success rate")

        self.assertEqual(snapshot.summary.memory_backend, "grep")
        self.assertEqual(snapshot.summary.memory_strategy, "full")
        self.assertIn("charging_success_rate", snapshot.prompt)


if __name__ == "__main__":
    unittest.main()

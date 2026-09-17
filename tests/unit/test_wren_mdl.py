from __future__ import annotations

import unittest
from pathlib import Path

from wren.context import build_json, validate_project

from packages.analytics_engine.validation import WrenSQLSecurityValidator
from packages.analytics_engine.wren_workflow import (
    WrenFirstWorkflow,
    WrenProjectContext,
)
from packages.domain import ValidationDecision
from packages.integrations import WrenSettings

PROJECT = Path("wren/ev_analytics")


class WrenMDLTests(unittest.TestCase):
    def test_layout_and_metadata_coverage(self) -> None:
        issues = validate_project(PROJECT)
        self.assertFalse(
            [issue for issue in issues if issue.level == "error"],
            issues,
        )

        manifest = build_json(PROJECT)
        self.assertEqual(manifest["layoutVersion"], 3)
        self.assertEqual(manifest["catalog"], "wren")
        self.assertEqual(manifest["schema"], "public")
        self.assertEqual(manifest["dataSource"], "postgres")
        self.assertEqual(len(manifest["models"]), 6)
        self.assertEqual(len(manifest["relationships"]), 0)
        self.assertEqual(sum(len(model["columns"]) for model in manifest["models"]), 102)

        for model in manifest["models"]:
            columns = model["columns"]
            self.assertTrue(
                all((column.get("properties") or {}).get("description") for column in columns),
                model["name"],
            )
            self.assertEqual(
                sum(column.get("isPrimaryKey") is True for column in columns),
                1,
                model["name"],
            )
            self.assertEqual(
                model["primaryKey"],
                next(column["name"] for column in columns if column.get("isPrimaryKey")),
            )

    def test_all_model_queries_dry_plan_and_pass_expanded_policy(self) -> None:
        context = WrenProjectContext(PROJECT).load()
        workflow = WrenFirstWorkflow(WrenSettings(wren_project_path=str(PROJECT)))
        validator = WrenSQLSecurityValidator()
        queries = {
            "customer_analytics_v1": "SELECT COUNT(*) FROM customer_analytics_v1 LIMIT 1",
            "vehicle_analytics_v1": "SELECT vehicle_status, COUNT(*) FROM vehicle_analytics_v1 GROUP BY vehicle_status LIMIT 100",
            "battery_health_analytics_v1": "SELECT AVG(state_of_health_pct) FROM battery_health_analytics_v1 LIMIT 1",
            "charging_session_analytics_v1": "SELECT session_status, COUNT(*) FROM charging_session_analytics_v1 GROUP BY session_status LIMIT 100",
            "charging_station_analytics_v1": "SELECT station_operational_status, COUNT(*) FROM charging_station_analytics_v1 GROUP BY station_operational_status LIMIT 100",
            "service_visit_analytics_v1": "SELECT visit_status, COUNT(*) FROM service_visit_analytics_v1 GROUP BY visit_status LIMIT 100",
        }

        for model_name, sql in queries.items():
            with self.subTest(model=model_name):
                planned_sql = workflow._dry_plan(context, sql)
                self.assertTrue(planned_sql.lstrip().upper().startswith("WITH"))
                report = validator.inspect(
                    planned_sql,
                    context.manifest,
                    stage="expanded",
                )
                self.assertEqual(report.decision, ValidationDecision.PASS)


if __name__ == "__main__":
    unittest.main()

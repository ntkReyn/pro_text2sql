from __future__ import annotations

import unittest

from packages.analytics_engine.validation import WrenSQLSecurityValidator

MANIFEST = {
    "models": [
        {
            "name": "customers",
            "tableReference": {"schema": "analytics", "table": "customers"},
        }
    ],
    "views": [],
    "cubes": [],
}


class WrenSQLSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = WrenSQLSecurityValidator()

    def test_logical_wren_model_is_allowed(self) -> None:
        report = self.validator.inspect(
            "SELECT COUNT(*) AS customer_count FROM customers LIMIT 10",
            MANIFEST,
            stage="logical",
        )

        self.assertEqual(report.decision.value, "pass")
        self.assertEqual(report.referenced_relations, ["customers"])

    def test_physical_relation_must_match_mdl(self) -> None:
        report = self.validator.inspect(
            "SELECT COUNT(*) FROM analytics.customers LIMIT 10",
            MANIFEST,
            stage="expanded",
        )

        self.assertEqual(report.decision.value, "pass")
        self.assertEqual(report.referenced_relations, ["analytics.customers"])

    def test_write_statement_and_missing_limit_are_rejected(self) -> None:
        write_report = self.validator.inspect(
            "DELETE FROM customers",
            MANIFEST,
            stage="logical",
        )
        no_limit_report = self.validator.inspect(
            "SELECT COUNT(*) FROM customers",
            MANIFEST,
            stage="logical",
        )

        self.assertEqual(write_report.error_code, "non_select_statement")
        self.assertEqual(no_limit_report.error_code, "row_limit_required")


if __name__ == "__main__":
    unittest.main()

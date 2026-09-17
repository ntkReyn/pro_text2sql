from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = PROJECT_ROOT / "data" / "seeds" / "0001_ev_enterprise_dataset.sql"
SCALE_SEED_PATH = PROJECT_ROOT / "data" / "seeds" / "0002_ev_enterprise_scale_dataset.sql"
MIGRATION_PATH = (
    PROJECT_ROOT / "db" / "migrations" / "0005_ev_enterprise_governance_columns.sql"
)
QUALITY_PATH = PROJECT_ROOT / "db" / "quality" / "ev_enterprise_quality_checks.sql"


class EVEnterpriseDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.seed = SEED_PATH.read_text(encoding="utf-8")
        cls.scale_seed = SCALE_SEED_PATH.read_text(encoding="utf-8")
        cls.migration = MIGRATION_PATH.read_text(encoding="utf-8")
        cls.quality = QUALITY_PATH.read_text(encoding="utf-8")

    def test_seed_has_six_domains_and_documented_row_volume(self) -> None:
        self.assertEqual(self.seed.count("INSERT INTO analytics."), 6)
        self.assertIn("customers 16, vehicles 20, battery snapshots 30", self.seed)
        self.assertIn("charging stations 6, charging sessions 32, service visits 20", self.seed)
        self.assertEqual(
            sum(int(value) for value in re.findall(r"generate_series\(1,\s*(\d+)", self.seed)),
            16 + 20 + 20 + 32 + 20,
        )

    def test_seed_covers_foreign_keys_and_operational_edge_cases(self) -> None:
        for token in ("CUS-ENT-", "VEH-ENT-", "STN-ENT-"):
            self.assertIn(token, self.seed)
        self.assertIn("CROSS JOIN LATERAL generate_series", self.seed)
        self.assertIn("WHEN number IN (16, 17, 18) THEN 'CUS-ENT-001'", self.seed)
        for edge_case in (
            "'inventory'",
            "'failed'",
            "'cancelled'",
            "'in_progress'",
            "'scheduled'",
            "'completed'",
        ):
            self.assertIn(edge_case, self.seed)

    def test_scale_seed_has_approximately_one_hundred_rows_per_domain(self) -> None:
        expected = (
            "customers 100, vehicles 125, battery snapshots 275",
            "charging stations 100, charging sessions 300, service visits 160",
        )
        for description in expected:
            self.assertIn(description, self.scale_seed)
        self.assertEqual(self.scale_seed.count("INSERT INTO analytics."), 6)
        self.assertIn("generate_series(1, 100)", self.scale_seed)
        self.assertIn("generate_series(1, 125)", self.scale_seed)
        self.assertIn("generate_series(1, 300)", self.scale_seed)
        self.assertIn("generate_series(1, 160)", self.scale_seed)
        self.assertIn("every non-inventory vehicle", self.scale_seed)

    def test_enterprise_columns_have_governance_and_integrity_controls(self) -> None:
        for field in (
            "customer_reference",
            "vehicle_identity_token",
            "connectivity_status",
            "data_quality_status",
            "station_external_ref",
            "payment_transaction_ref",
            "work_order_number",
            "parts_cost_amount",
        ):
            self.assertIn(f"ADD COLUMN {field}", self.migration)
        for constraint in (
            "dim_customer_customer_reference_uk",
            "dim_vehicle_asset_tag_uk",
            "charging_session_meter_check",
            "fact_charging_session_reference_uk",
            "fact_service_visit_work_order_uk",
        ):
            self.assertIn(constraint, self.migration)

    def test_quality_checks_cover_orphans_cardinality_and_business_rules(self) -> None:
        for check in (
            "orphan_vehicle_customer",
            "orphan_battery_vehicle",
            "orphan_charging_station",
            "cardinality_customer_vehicle",
            "cardinality_vehicle_battery",
            "completed charging sessions are valid",
        ):
            self.assertIn(check, self.quality)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.generate_ev_customer_data import generate_dataset, write_jsonl


class SyntheticDataTests(unittest.TestCase):
    def test_same_seed_produces_identical_dataset(self) -> None:
        first = generate_dataset(seed=42, customer_count=24)
        second = generate_dataset(seed=42, customer_count=24)

        self.assertEqual(first, second)

    def test_fixture_contains_required_domains_and_edge_cases(self) -> None:
        dataset = generate_dataset(seed=42, customer_count=24)

        self.assertEqual(len(dataset["customers"]), 24)
        self.assertLess(len(dataset["vehicles"]), len(dataset["customers"]))
        self.assertTrue(any(row["session_status"] == "failed" for row in dataset["charging_sessions"]))
        self.assertTrue(any(row["session_status"] == "cancelled" for row in dataset["charging_sessions"]))
        latest_soh = {}
        for row in dataset["battery_health_snapshots"]:
            latest_soh[row["vehicle_id"]] = row["state_of_health_pct"]
        self.assertTrue(any(value < 80 for value in latest_soh.values()))

    def test_generator_does_not_emit_direct_pii_fields(self) -> None:
        dataset = generate_dataset(seed=42, customer_count=12)
        forbidden = {"name", "email", "phone", "vin", "latitude", "longitude"}

        for rows in dataset.values():
            for row in rows:
                self.assertTrue(forbidden.isdisjoint(row))

    def test_jsonl_writer_creates_one_file_per_entity(self) -> None:
        dataset = generate_dataset(seed=42, customer_count=6)
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            write_jsonl(dataset, output_dir)
            self.assertEqual(
                {path.stem for path in output_dir.glob("*.jsonl")},
                set(dataset),
            )


if __name__ == "__main__":
    unittest.main()

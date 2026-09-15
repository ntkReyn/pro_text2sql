"""Generate deterministic, privacy-safe EV analytics data for local experiments."""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REGIONS = (("NORTH", "Ha Noi"), ("CENTRAL", "Da Nang"), ("SOUTH", "Ho Chi Minh"))
MODELS = ("VF5", "VF6", "VF8")


def generate_dataset(*, seed: int = 42, customer_count: int = 24) -> dict[str, list[dict[str, Any]]]:
    """Return stable synthetic rows. No name, email, phone, VIN, or precise GPS is emitted."""

    if customer_count < 3:
        raise ValueError("customer_count must be at least 3")
    rng = random.Random(seed)
    base_time = datetime(2026, 7, 1, 0, 0, tzinfo=timezone.utc)

    customers: list[dict[str, Any]] = []
    vehicles: list[dict[str, Any]] = []
    battery_snapshots: list[dict[str, Any]] = []
    charging_sessions: list[dict[str, Any]] = []
    service_visits: list[dict[str, Any]] = []

    stations = [
        {
            "charging_station_id": f"ST-{index + 1:03d}",
            "station_name": f"Synthetic Station {index + 1:02d}",
            "station_scope": ("public", "dealer", "workplace")[index],
            "region_code": region,
            "province_name": province,
            "connector_type": "DC_CCS2" if index != 2 else "AC_TYPE2",
            "operational_status": "maintenance" if index == 1 else "operational",
        }
        for index, (region, province) in enumerate(REGIONS)
    ]

    for index in range(customer_count):
        customer_id = f"CUS-{index + 1:05d}"
        region, _ = REGIONS[index % len(REGIONS)]
        customers.append(
            {
                "customer_id": customer_id,
                "customer_type": "fleet" if index % 8 == 0 else "individual",
                "customer_segment": "fleet" if index % 8 == 0 else ("premium" if index % 3 == 0 else "standard"),
                "home_region_code": region,
                "customer_status": "inactive" if index % 11 == 0 else "active",
                "analytics_consent": index % 5 != 0,
            }
        )

        # Preserve a no-vehicle cohort for left-join and denominator tests.
        if index % 7 == 0:
            continue

        vehicle_id = f"VEH-{index + 1:05d}"
        model = MODELS[index % len(MODELS)]
        vehicles.append(
            {
                "vehicle_id": vehicle_id,
                "current_customer_id": customer_id,
                "vehicle_model_code": model,
                "model_year": 2023 + index % 4,
                "battery_nominal_capacity_kwh": (37.2, 59.6, 87.7)[index % 3],
                "current_status": "in_service" if index % 10 == 0 else "active",
            }
        )

        starting_soh = 98.0 - (index % 9) * 1.8
        if index == customer_count - 1:
            starting_soh = 80.3
        for observation in range(3):
            observed_at = base_time + timedelta(days=observation * 30, hours=index)
            soh = round(starting_soh - observation * rng.uniform(0.2, 0.7), 2)
            battery_snapshots.append(
                {
                    "battery_snapshot_id": f"BAT-{index + 1:05d}-{observation + 1}",
                    "vehicle_id": vehicle_id,
                    "battery_pack_key": f"PACK-{index + 1:05d}",
                    "observed_at": observed_at.isoformat(),
                    "state_of_charge_pct": round(rng.uniform(12, 96), 2),
                    "state_of_health_pct": soh,
                    "cycle_count": 40 + index * 9 + observation * 5,
                    "pack_temperature_c": round(rng.uniform(20, 44), 2),
                }
            )

        for attempt in range(3):
            started_at = base_time + timedelta(days=(index * 4 + attempt * 9) % 88, hours=8 + attempt)
            status = "completed"
            if attempt == 1 and index % 4 == 0:
                status = "failed"
            elif attempt == 2 and index % 6 == 0:
                status = "cancelled"
            energy = round(rng.uniform(8, 58), 3) if status == "completed" else 0.0
            charging_sessions.append(
                {
                    "charging_session_id": f"CHG-{index + 1:05d}-{attempt + 1}",
                    "vehicle_id": vehicle_id,
                    "charging_station_id": stations[(index + attempt) % len(stations)]["charging_station_id"],
                    "started_at": started_at.isoformat(),
                    "ended_at": (started_at + timedelta(minutes=35 + attempt * 20)).isoformat(),
                    "session_status": status,
                    "energy_delivered_kwh": energy,
                }
            )

        if index % 2 == 0:
            opened_at = base_time + timedelta(days=(index * 5) % 88, hours=2)
            service_visits.append(
                {
                    "service_visit_id": f"SVC-{index + 1:05d}",
                    "vehicle_id": vehicle_id,
                    "service_center_code": f"SC-{index % 3 + 1:02d}",
                    "opened_at": opened_at.isoformat(),
                    "completed_at": (opened_at + timedelta(hours=5)).isoformat(),
                    "visit_status": "completed",
                    "visit_type": "repair" if index % 4 == 0 else "maintenance",
                    "issue_category": "battery" if index % 4 == 0 else "inspection",
                    "is_repeat_issue": index % 6 == 0,
                }
            )

    return {
        "customers": customers,
        "vehicles": vehicles,
        "battery_health_snapshots": battery_snapshots,
        "charging_stations": stations,
        "charging_sessions": charging_sessions,
        "service_visits": service_visits,
    }


def write_jsonl(dataset: dict[str, list[dict[str, Any]]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for entity, rows in dataset.items():
        target = output_dir / f"{entity}.jsonl"
        with target.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--customers", type=int, default=24)
    parser.add_argument("--output-dir", type=Path, default=Path("data/local/generated"))
    args = parser.parse_args()
    dataset = generate_dataset(seed=args.seed, customer_count=args.customers)
    write_jsonl(dataset, args.output_dir)
    print(json.dumps({name: len(rows) for name, rows in dataset.items()}, sort_keys=True))


if __name__ == "__main__":
    main()

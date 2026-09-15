"""Evaluate the deterministic Week 1 planner against reviewed semantic plans."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from packages.analytics_engine.planning import BaselinePlanner, PlanningStatus
from packages.analytics_engine.sql_generation import PostgreSQLSemanticCompiler
from packages.semantic_layer import load_default_catalog


def evaluate(dataset_path: Path) -> dict[str, object]:
    catalog = load_default_catalog()
    planner = BaselinePlanner(catalog)
    compiler = PostgreSQLSemanticCompiler(catalog)
    cases = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    details: list[dict[str, object]] = []
    for case in cases:
        result = planner.plan(case["question"])
        plan_match = (
            result.status is PlanningStatus.PLANNED
            and result.plan is not None
            and result.plan.model_dump(mode="json") == case["expected_plan"]
        )
        compile_ok = False
        if result.plan is not None:
            compiler.compile(result.plan, allow_draft_metrics=True)
            compile_ok = True
        details.append(
            {
                "case_id": case["case_id"],
                "status": result.status.value,
                "plan_exact_match": plan_match,
                "compile_ok": compile_ok,
            }
        )

    return {
        "dataset": str(dataset_path),
        "case_count": len(details),
        "planned_count": sum(item["status"] == "planned" for item in details),
        "exact_plan_count": sum(bool(item["plan_exact_match"]) for item in details),
        "compile_success_count": sum(bool(item["compile_ok"]) for item in details),
        "execution_evaluated": False,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT / "evals" / "datasets" / "ev_customer_v1.jsonl",
    )
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()
    report = evaluate(args.dataset)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

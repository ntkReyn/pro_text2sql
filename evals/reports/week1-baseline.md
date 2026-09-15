# Week 1 deterministic baseline

Evaluation date: 2026-09-15  
Dataset: `evals/datasets/ev_customer_v1.jsonl`  
Baseline: `BaselinePlanner` → `SemanticQueryPlan` → `PostgreSQLSemanticCompiler`

## Result

| Check | Result | Interpretation |
|---|---:|---|
| Reviewed questions | 16 | Covers customer, vehicle, battery, station/charging and service |
| Planned | 16/16 | Every in-scope fixture produced a typed plan |
| Exact expected-plan match | 16/16 | Metric, dimensions, filters, time, sort and limit matched |
| PostgreSQL compile | 16/16 | All plans passed semantic validation and compiled |
| Automated tests | 21/21 | Unit and FastAPI integration tests passed |
| Database execution/result equivalence | Not run | Requires migrated PostgreSQL fixture; Gate B remains open |

This is an intentionally narrow, rule-based B0 result on a reviewed fixture, not evidence of generalization. The next comparison must keep this dataset fixed and report B0 versus graph/value retrieval, Wren parity and Datus/Semantic-DAIL planning separately.

Reproduce with:

```powershell
python scripts/evaluate_baseline.py
python -m unittest discover -s tests -v
```

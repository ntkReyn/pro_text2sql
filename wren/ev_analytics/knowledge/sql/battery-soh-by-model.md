---
nl: What is the average latest battery state of health by vehicle model?
sql: |
  SELECT vehicle_model_code, AVG(state_of_health_pct) AS average_latest_battery_soh_pct
  FROM battery_health_analytics_v1
  GROUP BY vehicle_model_code
  LIMIT 100
datasource: postgres
tags:
  - battery_health
  - state_of_health
  - canonical_metric
source: curated
---

This is descriptive latest-snapshot health, not a failure prediction.

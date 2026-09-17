---
nl: How many vehicles are there by current vehicle status?
sql: |
  SELECT vehicle_status, COUNT(*) AS vehicle_count
  FROM vehicle_analytics_v1
  GROUP BY vehicle_status
  LIMIT 100
datasource: postgres
tags:
  - vehicle_count
  - status
  - canonical_metric
source: curated
---

Use the current vehicle mart grain: one row per current vehicle.

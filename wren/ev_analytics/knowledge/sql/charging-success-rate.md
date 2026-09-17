---
nl: What is the charging success rate by station region?
sql: |
  SELECT station_region_code,
         100.0 * COUNT(*) FILTER (WHERE session_status = 'completed' AND energy_delivered_kwh > 0)
           / NULLIF(COUNT(*) FILTER (WHERE session_status IN ('completed', 'failed')), 0)
           AS charging_success_rate
  FROM charging_session_analytics_v1
  GROUP BY station_region_code
  LIMIT 100
datasource: postgres
tags:
  - charging_success_rate
  - charging
  - canonical_metric
source: curated
---

The denominator is completed or failed attempts; positive delivered energy is required for success.

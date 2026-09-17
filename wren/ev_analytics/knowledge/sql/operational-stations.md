---
nl: How many charging stations are operational by province?
sql: |
  SELECT province_name,
         COUNT(*) FILTER (WHERE station_operational_status = 'operational') AS operational_charging_station_count
  FROM charging_station_analytics_v1
  GROUP BY province_name
  LIMIT 100
datasource: postgres
tags:
  - operational_charging_station_count
  - charging_station
  - canonical_metric
source: curated
---

The station mart grain is one station, not one connector port.

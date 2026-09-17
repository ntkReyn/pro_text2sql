---
nl: How many service visits were completed by service issue category?
sql: |
  SELECT service_issue_category, COUNT(*) FILTER (WHERE visit_status = 'completed') AS completed_service_visit_count
  FROM service_visit_analytics_v1
  GROUP BY service_issue_category
  LIMIT 100
datasource: postgres
tags:
  - completed_service_visit_count
  - service
  - canonical_metric
source: curated
---

Use visit_status for completion; do not infer completion from timestamps.

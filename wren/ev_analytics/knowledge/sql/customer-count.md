---
nl: How many customers are in the analytics customer mart?
sql: |
  SELECT COUNT(*) AS customer_count
  FROM customer_analytics_v1
  LIMIT 1
datasource: postgres
tags:
  - customer_count
  - canonical_metric
source: curated
---

Use the customer mart grain: one row per customer, including customers without a vehicle.

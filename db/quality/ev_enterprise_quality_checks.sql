-- Read-only audit queries for the six-table synthetic EV dataset.
-- Run with a read-only analytics connection after migration.

SELECT 'row_counts' AS check_group, table_name, row_count
FROM (
    SELECT 'dim_customer' AS table_name, COUNT(*) AS row_count FROM analytics.dim_customer
    UNION ALL SELECT 'dim_vehicle', COUNT(*) FROM analytics.dim_vehicle
    UNION ALL SELECT 'fact_battery_health_snapshot', COUNT(*) FROM analytics.fact_battery_health_snapshot
    UNION ALL SELECT 'dim_charging_station', COUNT(*) FROM analytics.dim_charging_station
    UNION ALL SELECT 'fact_charging_session', COUNT(*) FROM analytics.fact_charging_session
    UNION ALL SELECT 'fact_service_visit', COUNT(*) FROM analytics.fact_service_visit
) AS counts
ORDER BY table_name;

SELECT 'orphan_vehicle_customer' AS check_name, COUNT(*) AS violations
FROM analytics.dim_vehicle AS vehicle
LEFT JOIN analytics.dim_customer AS customer
    ON customer.customer_id = vehicle.current_customer_id
WHERE vehicle.current_customer_id IS NOT NULL AND customer.customer_id IS NULL
UNION ALL
SELECT 'orphan_battery_vehicle', COUNT(*)
FROM analytics.fact_battery_health_snapshot AS battery
LEFT JOIN analytics.dim_vehicle AS vehicle ON vehicle.vehicle_id = battery.vehicle_id
WHERE vehicle.vehicle_id IS NULL
UNION ALL
SELECT 'orphan_charging_vehicle', COUNT(*)
FROM analytics.fact_charging_session AS session
LEFT JOIN analytics.dim_vehicle AS vehicle ON vehicle.vehicle_id = session.vehicle_id
WHERE vehicle.vehicle_id IS NULL
UNION ALL
SELECT 'orphan_charging_station', COUNT(*)
FROM analytics.fact_charging_session AS session
LEFT JOIN analytics.dim_charging_station AS station
    ON station.charging_station_id = session.charging_station_id
WHERE station.charging_station_id IS NULL
UNION ALL
SELECT 'orphan_service_vehicle', COUNT(*)
FROM analytics.fact_service_visit AS visit
LEFT JOIN analytics.dim_vehicle AS vehicle ON vehicle.vehicle_id = visit.vehicle_id
WHERE vehicle.vehicle_id IS NULL;

SELECT 'cardinality_customer_vehicle' AS relationship,
       COUNT(*) FILTER (WHERE vehicle_count = 0) AS customers_without_vehicle,
       COUNT(*) FILTER (WHERE vehicle_count = 1) AS one_to_one_customers,
       COUNT(*) FILTER (WHERE vehicle_count > 1) AS one_to_many_customers
FROM (
    SELECT customer.customer_id, COUNT(vehicle.vehicle_id) AS vehicle_count
    FROM analytics.dim_customer AS customer
    LEFT JOIN analytics.dim_vehicle AS vehicle
        ON vehicle.current_customer_id = customer.customer_id
    GROUP BY customer.customer_id
) AS customer_vehicle_counts;

SELECT 'cardinality_vehicle_battery' AS relationship,
       COUNT(*) AS vehicles_with_snapshot,
       COUNT(*) FILTER (WHERE snapshot_count = 1) AS one_to_one_current_snapshots,
       COUNT(*) FILTER (WHERE snapshot_count > 1) AS one_to_many_history_vehicles
FROM (
    SELECT vehicle.vehicle_id, COUNT(battery.battery_snapshot_id) AS snapshot_count
    FROM analytics.dim_vehicle AS vehicle
    LEFT JOIN analytics.fact_battery_health_snapshot AS battery
        ON battery.vehicle_id = vehicle.vehicle_id
    GROUP BY vehicle.vehicle_id
) AS vehicle_battery_counts
WHERE snapshot_count > 0;

WITH charging_vehicles AS (
    SELECT DISTINCT vehicle_id FROM analytics.fact_charging_session
), service_vehicles AS (
    SELECT DISTINCT vehicle_id FROM analytics.fact_service_visit
)
SELECT 'cardinality_vehicle_operations' AS relationship,
       (SELECT COUNT(*) FROM charging_vehicles) AS vehicles_with_charging,
       (SELECT COUNT(*) FROM service_vehicles) AS vehicles_with_service,
       (SELECT COUNT(*)
        FROM charging_vehicles AS charging
        INNER JOIN service_vehicles AS service USING (vehicle_id))
           AS charging_to_service_joinable_vehicle_count;

SELECT 'business_check' AS check_name, 'completed charging sessions are valid' AS rule,
       COUNT(*) AS violations
FROM analytics.fact_charging_session
WHERE session_status = 'completed'
  AND (ended_at IS NULL OR end_soc_pct IS NULL OR energy_delivered_kwh <= 0)
UNION ALL
SELECT 'business_check', 'completed service visits are closed', COUNT(*)
FROM analytics.fact_service_visit
WHERE visit_status = 'completed' AND completed_at IS NULL
UNION ALL
SELECT 'business_check', 'readings are within battery range', COUNT(*)
FROM analytics.fact_battery_health_snapshot
WHERE state_of_health_pct NOT BETWEEN 0 AND 100
   OR state_of_charge_pct NOT BETWEEN 0 AND 100;

CREATE VIEW analytics.customer_analytics_v1 AS
SELECT
    customer.customer_id,
    customer.customer_type,
    customer.customer_segment,
    customer.age_band,
    customer.home_region_code AS customer_region_code,
    customer.joined_on,
    customer.customer_status,
    customer.analytics_consent,
    COUNT(vehicle.vehicle_id) AS vehicle_count,
    customer.source_updated_at,
    now() AS model_built_at
FROM analytics.dim_customer AS customer
LEFT JOIN analytics.dim_vehicle AS vehicle
    ON vehicle.current_customer_id = customer.customer_id
GROUP BY
    customer.customer_id,
    customer.customer_type,
    customer.customer_segment,
    customer.age_band,
    customer.home_region_code,
    customer.joined_on,
    customer.customer_status,
    customer.analytics_consent,
    customer.source_updated_at;

COMMENT ON VIEW analytics.customer_analytics_v1 IS
    'Semantic mart. Grain: one synthetic customer, including customers without a current vehicle.';

CREATE VIEW analytics.vehicle_analytics_v1 AS
SELECT
    vehicle_id,
    vehicle_model_code,
    model_year,
    vehicle_status,
    customer_id,
    customer_segment,
    home_region_code AS customer_region_code,
    customer_status,
    state_of_health_pct,
    source_updated_at,
    model_built_at
FROM analytics.customer_vehicle_overview_v1;

COMMENT ON VIEW analytics.vehicle_analytics_v1 IS
    'Semantic mart. Grain: one current vehicle with normalized customer-region naming.';

CREATE VIEW analytics.battery_health_analytics_v1 AS
WITH latest_battery AS (
    SELECT DISTINCT ON (snapshot.vehicle_id)
        snapshot.*
    FROM analytics.fact_battery_health_snapshot AS snapshot
    ORDER BY snapshot.vehicle_id, snapshot.observed_at DESC
)
SELECT
    battery.battery_snapshot_id,
    battery.battery_pack_key,
    battery.observed_at,
    battery.state_of_charge_pct,
    battery.state_of_health_pct,
    battery.usable_capacity_kwh,
    battery.cycle_count,
    battery.pack_temperature_c,
    battery.odometer_km,
    vehicle.vehicle_id,
    vehicle.vehicle_model_code,
    vehicle.model_year,
    vehicle.current_status AS vehicle_status,
    customer.customer_id,
    customer.customer_segment,
    customer.home_region_code AS customer_region_code,
    GREATEST(
        battery.source_updated_at,
        vehicle.source_updated_at,
        COALESCE(customer.source_updated_at, '-infinity'::timestamptz)
    ) AS source_updated_at,
    now() AS model_built_at
FROM latest_battery AS battery
INNER JOIN analytics.dim_vehicle AS vehicle
    ON vehicle.vehicle_id = battery.vehicle_id
LEFT JOIN analytics.dim_customer AS customer
    ON customer.customer_id = vehicle.current_customer_id;

COMMENT ON VIEW analytics.battery_health_analytics_v1 IS
    'Semantic mart. Grain: latest available battery-health snapshot per vehicle; descriptive, not predictive.';

CREATE VIEW analytics.service_visit_analytics_v1 AS
SELECT
    visit.service_visit_id,
    visit.opened_at,
    visit.completed_at,
    visit.visit_status,
    visit.visit_type,
    visit.issue_category AS service_issue_category,
    visit.service_center_code,
    visit.odometer_km,
    visit.warranty_covered,
    visit.is_repeat_issue,
    visit.customer_paid_amount,
    visit.currency_code,
    visit.satisfaction_score,
    vehicle.vehicle_id,
    vehicle.vehicle_model_code,
    vehicle.model_year,
    customer.customer_id,
    customer.customer_segment,
    customer.home_region_code AS customer_region_code,
    GREATEST(
        visit.source_updated_at,
        vehicle.source_updated_at,
        COALESCE(customer.source_updated_at, '-infinity'::timestamptz)
    ) AS source_updated_at,
    now() AS model_built_at
FROM analytics.fact_service_visit AS visit
INNER JOIN analytics.dim_vehicle AS vehicle
    ON vehicle.vehicle_id = visit.vehicle_id
LEFT JOIN analytics.dim_customer AS customer
    ON customer.customer_id = vehicle.current_customer_id;

COMMENT ON VIEW analytics.service_visit_analytics_v1 IS
    'Semantic mart. Grain: one service visit enriched with current vehicle and synthetic customer attributes.';

CREATE VIEW analytics.charging_station_analytics_v1 AS
SELECT
    station.charging_station_id,
    station.station_name,
    station.operator_code,
    station.station_scope,
    station.region_code AS station_region_code,
    station.province_name,
    station.primary_connector_type AS connector_type,
    station.maximum_power_kw,
    station.charging_port_count,
    station.operational_status AS station_operational_status,
    station.commissioned_on,
    station.source_updated_at,
    now() AS model_built_at
FROM analytics.dim_charging_station AS station;

COMMENT ON VIEW analytics.charging_station_analytics_v1 IS
    'Semantic mart. Grain: one synthetic charging station.';

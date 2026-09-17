-- Deterministic synthetic enterprise dataset for the EV operating model.
--
-- This seed adds 124 rows without touching the existing lab fixture:
--   customers 16, vehicles 20, battery snapshots 30,
--   charging stations 6, charging sessions 32, service visits 20.
-- The identifiers use the ENT namespace so the seed can be applied to a
-- database that already contains the smaller LAB fixture.

INSERT INTO analytics.dim_customer (
    customer_id,
    customer_reference,
    customer_type,
    customer_segment,
    age_band,
    home_region_code,
    preferred_language,
    joined_on,
    customer_status,
    analytics_consent,
    country_code,
    acquisition_channel,
    consent_updated_at,
    source_updated_at,
    created_at,
    updated_at
)
SELECT
    'CUS-ENT-' || to_char(number, 'FM000'),
    'CRM-ENT-' || to_char(number, 'FM000'),
    CASE
        WHEN number % 8 = 0 THEN 'fleet'
        WHEN number % 5 = 0 THEN 'corporate'
        ELSE 'individual'
    END,
    CASE
        WHEN number % 8 = 0 THEN 'fleet'
        WHEN number % 3 = 0 THEN 'premium'
        ELSE 'standard'
    END,
    CASE
        WHEN number % 8 = 0 OR number % 5 = 0 THEN NULL
        ELSE (ARRAY['18_24', '25_34', '35_44', '45_54', '55_plus'])[(number - 1) % 5 + 1]
    END,
    (ARRAY['NORTH', 'CENTRAL', 'SOUTH'])[(number - 1) % 3 + 1],
    CASE WHEN number % 4 = 0 THEN 'en' ELSE 'vi' END,
    date '2023-01-01' + number * 23,
    CASE WHEN number IN (15, 16) THEN 'inactive' ELSE 'active' END,
    number % 5 <> 0,
    'VN',
    (ARRAY['direct', 'dealer', 'fleet_sales', 'partner', 'online'])[(number - 1) % 5 + 1],
    CASE WHEN number % 5 <> 0 THEN timestamptz '2026-09-01 01:00:00+00' + number * INTERVAL '3 hours' END,
    timestamptz '2026-09-10 01:00:00+00' + number * INTERVAL '1 hour',
    (date '2023-01-01' + number * 23)::timestamptz,
    timestamptz '2026-09-10 01:00:00+00' + number * INTERVAL '1 hour'
FROM generate_series(1, 16) AS series(number);

INSERT INTO analytics.dim_vehicle (
    vehicle_id,
    current_customer_id,
    vehicle_asset_tag,
    vehicle_identity_token,
    vehicle_model_code,
    model_year,
    manufactured_on,
    delivered_on,
    battery_nominal_capacity_kwh,
    current_status,
    software_version,
    warranty_start_on,
    warranty_end_on,
    connectivity_status,
    source_updated_at
)
SELECT
    'VEH-ENT-' || to_char(number, 'FM000'),
    CASE
        WHEN number <= 15 THEN 'CUS-ENT-' || to_char(number, 'FM000')
        WHEN number IN (16, 17, 18) THEN 'CUS-ENT-001'
        WHEN number = 19 THEN 'CUS-ENT-002'
        ELSE NULL
    END,
    'ASSET-ENT-' || to_char(number, 'FM000'),
    'SYN-' || md5('vehicle-ent-' || number::text),
    (ARRAY['VF5', 'VF6', 'VF8', 'VF9'])[(number - 1) % 4 + 1],
    2023 + (number % 4),
    date '2023-01-01' + number * 17,
    CASE WHEN number = 20 THEN NULL ELSE date '2023-01-01' + number * 17 + 35 END,
    (ARRAY[37.20, 59.60, 87.70, 90.00])[(number - 1) % 4 + 1],
    CASE
        WHEN number = 20 THEN 'inventory'
        WHEN number % 6 = 0 THEN 'in_service'
        WHEN number = 19 THEN 'inactive'
        ELSE 'active'
    END,
    'v' || (1 + number % 3)::text || '.' || (number % 10)::text || '.0',
    CASE WHEN number = 20 THEN NULL ELSE date '2023-01-01' + number * 17 + 35 END,
    CASE WHEN number = 20 THEN NULL ELSE date '2023-01-01' + number * 17 + 35 + 1460 END,
    CASE
        WHEN number % 9 = 0 THEN 'offline'
        WHEN number % 5 = 0 THEN 'degraded'
        ELSE 'online'
    END,
    timestamptz '2026-09-11 01:00:00+00' + number * INTERVAL '2 hours'
FROM generate_series(1, 20) AS series(number);

INSERT INTO analytics.fact_battery_health_snapshot (
    battery_snapshot_id,
    vehicle_id,
    battery_pack_key,
    observed_at,
    state_of_charge_pct,
    state_of_health_pct,
    usable_capacity_kwh,
    cycle_count,
    pack_temperature_c,
    odometer_km,
    data_quality_status,
    measurement_source,
    degradation_rate_pct_per_1000_cycles,
    source_updated_at
)
SELECT
    'BAT-ENT-' || to_char(vehicle_number, 'FM000') || '-' || observation_number,
    'VEH-ENT-' || to_char(vehicle_number, 'FM000'),
    'PACK-ENT-' || to_char(vehicle_number, 'FM000') ||
        CASE WHEN vehicle_number = 7 AND observation_number = 2 THEN '-R2' ELSE '-R1' END,
    timestamptz '2026-08-01 06:00:00+00'
        + vehicle_number * INTERVAL '2 hours'
        + (observation_number - 1) * INTERVAL '30 days',
    (18 + ((vehicle_number * 13 + observation_number * 7) % 72))::numeric,
    round((99.2 - vehicle_number * 0.62 - (observation_number - 1) * 1.15)::numeric, 2),
    round((ARRAY[37.20, 59.60, 87.70, 90.00])[(vehicle_number - 1) % 4 + 1]
        * (99.2 - vehicle_number * 0.62 - (observation_number - 1) * 1.15) / 100, 2),
    45 + vehicle_number * 14 + observation_number * 6,
    round((24 + ((vehicle_number * 3 + observation_number) % 16))::numeric, 2),
    vehicle_number * 1250 + observation_number * 180,
    CASE WHEN vehicle_number IN (7, 14) AND observation_number = 2 THEN 'estimated' ELSE 'validated' END,
    CASE WHEN observation_number = 2 THEN 'telemetry' ELSE 'bms' END,
    round((0.8 + vehicle_number * 0.04)::numeric, 3),
    timestamptz '2026-08-01 06:15:00+00'
        + vehicle_number * INTERVAL '2 hours'
        + (observation_number - 1) * INTERVAL '30 days'
FROM generate_series(1, 20) AS vehicles(vehicle_number)
CROSS JOIN LATERAL generate_series(
    1,
    CASE WHEN vehicles.vehicle_number <= 10 THEN 2 ELSE 1 END
) AS observations(observation_number);

INSERT INTO analytics.dim_charging_station (
    charging_station_id,
    station_external_ref,
    station_name,
    operator_code,
    station_scope,
    region_code,
    province_name,
    city_name,
    primary_connector_type,
    maximum_power_kw,
    charging_port_count,
    operational_status,
    network_status,
    commissioned_on,
    last_heartbeat_at,
    source_updated_at
)
VALUES
    ('STN-ENT-001', 'STATION-ENT-001', 'Enterprise Ha Noi Hub', 'OP-ENT-NORTH', 'public', 'NORTH', 'Ha Noi', 'Ha Noi', 'DC_CCS2', 180.00, 12, 'operational', 'online', '2024-01-15', '2026-09-16T01:00:00+00', '2026-09-16T01:05:00+00'),
    ('STN-ENT-002', 'STATION-ENT-002', 'Enterprise Bac Ninh Depot', 'OP-ENT-NORTH', 'dealer', 'NORTH', 'Bac Ninh', 'Bac Ninh', 'DC_CCS2', 120.00, 8, 'operational', 'online', '2024-03-20', '2026-09-16T01:01:00+00', '2026-09-16T01:05:00+00'),
    ('STN-ENT-003', 'STATION-ENT-003', 'Enterprise Da Nang Hub', 'OP-ENT-CENTRAL', 'public', 'CENTRAL', 'Da Nang', 'Da Nang', 'DC_CCS2', 150.00, 10, 'operational', 'degraded', '2024-02-10', '2026-09-15T20:00:00+00', '2026-09-16T01:05:00+00'),
    ('STN-ENT-004', 'STATION-ENT-004', 'Enterprise Quang Nam Workplace', 'OP-ENT-CENTRAL', 'workplace', 'CENTRAL', 'Quang Nam', 'Hoi An', 'AC_TYPE2', 22.00, 16, 'maintenance', 'offline', '2024-06-01', '2026-09-14T13:00:00+00', '2026-09-16T01:05:00+00'),
    ('STN-ENT-005', 'STATION-ENT-005', 'Enterprise Ho Chi Minh Hub', 'OP-ENT-SOUTH', 'public', 'SOUTH', 'Ho Chi Minh City', 'Ho Chi Minh City', 'DC_CCS2', 250.00, 20, 'operational', 'online', '2024-01-05', '2026-09-16T01:02:00+00', '2026-09-16T01:05:00+00'),
    ('STN-ENT-006', 'STATION-ENT-006', 'Enterprise Binh Duong Fleet Yard', 'OP-ENT-SOUTH', 'home', 'SOUTH', 'Binh Duong', 'Thu Dau Mot', 'AC_TYPE2', 11.00, 4, 'operational', 'online', '2024-08-15', '2026-09-16T01:03:00+00', '2026-09-16T01:05:00+00');

WITH session_rows AS (
    SELECT
        number,
        ((number - 1) % 20) + 1 AS vehicle_number,
        ((number - 1) % 6) + 1 AS station_number,
        CASE
            WHEN number % 8 IN (1, 2, 3, 4, 0) THEN 'completed'
            WHEN number % 8 = 5 THEN 'failed'
            WHEN number % 8 = 6 THEN 'cancelled'
            ELSE 'in_progress'
        END AS session_status,
        timestamptz '2026-07-03 02:00:00+00' + number * INTERVAL '2 days' AS started_at,
        (15 + (number * 7 % 45))::numeric AS start_soc_pct
    FROM generate_series(1, 32) AS series(number)
), calculated AS (
    SELECT
        session_rows.*,
        CASE WHEN session_status IN ('completed', 'failed', 'cancelled')
            THEN started_at + CASE
                WHEN session_status = 'completed' THEN INTERVAL '42 minutes'
                WHEN session_status = 'failed' THEN INTERVAL '5 minutes'
                ELSE INTERVAL '1 minute'
            END
        END AS ended_at,
        CASE WHEN session_status = 'completed'
            THEN start_soc_pct + (25 + number % 4 * 5)
            WHEN session_status = 'failed' THEN start_soc_pct
        END AS end_soc_pct,
        CASE WHEN session_status = 'completed' THEN round((22 + number % 5 * 4)::numeric, 3)
            WHEN session_status = 'failed' THEN 0.500::numeric
            WHEN session_status = 'in_progress' THEN 2.000::numeric
            ELSE 0.000::numeric
        END AS energy_delivered_kwh
    FROM session_rows
)
INSERT INTO analytics.fact_charging_session (
    charging_session_id,
    session_reference,
    vehicle_id,
    charging_station_id,
    started_at,
    ended_at,
    session_status,
    start_soc_pct,
    end_soc_pct,
    energy_delivered_kwh,
    peak_power_kw,
    billing_status,
    cost_amount,
    currency_code,
    stop_reason,
    connector_id,
    firmware_version,
    error_code,
    meter_start_kwh,
    meter_end_kwh,
    payment_transaction_ref,
    data_quality_status,
    source_updated_at
)
SELECT
    'CHG-ENT-' || to_char(number, 'FM000'),
    'SESSION-ENT-' || to_char(number, 'FM000'),
    'VEH-ENT-' || to_char(vehicle_number, 'FM000'),
    'STN-ENT-' || to_char(station_number, 'FM000'),
    started_at,
    ended_at,
    session_status,
    start_soc_pct,
    end_soc_pct,
    energy_delivered_kwh,
    CASE WHEN session_status = 'cancelled' THEN NULL ELSE 18 + number % 8 * 12 END,
    CASE
        WHEN session_status <> 'completed' THEN 'not_applicable'
        WHEN number % 3 = 1 THEN 'billed'
        WHEN number % 3 = 2 THEN 'free'
        ELSE 'unknown'
    END,
    CASE
        WHEN session_status = 'completed' AND number % 3 = 1
            THEN round(energy_delivered_kwh * 4200, 2)
        WHEN session_status = 'completed' AND number % 3 = 2 THEN 0
        ELSE NULL
    END,
    CASE WHEN session_status = 'completed' AND number % 3 IN (1, 2) THEN 'VND' ELSE NULL END,
    CASE
        WHEN session_status = 'completed' THEN CASE WHEN number % 2 = 0 THEN 'target_soc' ELSE 'user_stop' END
        WHEN session_status = 'failed' THEN 'station_fault'
        WHEN session_status = 'cancelled' THEN 'user_cancelled'
        ELSE 'ongoing'
    END,
    'CON-' || to_char(((number - 1) % 6) + 1, 'FM00'),
    'fw-' || (2 + number % 3)::text || '.' || (number % 10)::text,
    CASE WHEN session_status = 'failed' THEN 'E-' || to_char(100 + number, 'FM000') ELSE NULL END,
    number * 100.000,
    CASE WHEN session_status IN ('completed', 'failed') THEN number * 100.000 + energy_delivered_kwh END,
    CASE WHEN session_status = 'completed' AND number % 3 = 1 THEN 'PAY-ENT-' || to_char(number, 'FM000') END,
    CASE WHEN number IN (11, 27) THEN 'estimated' ELSE 'validated' END,
    COALESCE(ended_at, started_at) + INTERVAL '5 minutes'
FROM calculated;

WITH service_rows AS (
    SELECT
        number,
        CASE
            WHEN number % 7 = 0 THEN 'cancelled'
            WHEN number % 7 = 1 THEN 'scheduled'
            WHEN number % 7 = 2 THEN 'in_progress'
            ELSE 'completed'
        END AS visit_status,
        ((number - 1) % 20) + 1 AS vehicle_number,
        timestamptz '2026-07-05 03:00:00+00' + number * INTERVAL '3 days' AS opened_at
    FROM generate_series(1, 20) AS series(number)
)
INSERT INTO analytics.fact_service_visit (
    service_visit_id,
    work_order_number,
    vehicle_id,
    service_center_code,
    opened_at,
    completed_at,
    visit_status,
    visit_type,
    issue_category,
    odometer_km,
    warranty_covered,
    is_repeat_issue,
    customer_paid_amount,
    currency_code,
    satisfaction_score,
    service_priority,
    root_cause_code,
    resolution_code,
    technician_team_code,
    parts_cost_amount,
    parts_currency_code,
    source_updated_at
)
SELECT
    'SRV-ENT-' || to_char(number, 'FM000'),
    'WO-ENT-' || to_char(number, 'FM000'),
    'VEH-ENT-' || to_char(vehicle_number, 'FM000'),
    'SC-ENT-' || to_char(((vehicle_number - 1) % 4) + 1, 'FM00'),
    opened_at,
    CASE WHEN visit_status IN ('completed', 'cancelled')
        THEN opened_at + CASE WHEN visit_status = 'completed' THEN INTERVAL '5 hours' ELSE INTERVAL '1 hour' END
    END,
    visit_status,
    CASE number % 4
        WHEN 0 THEN 'maintenance'
        WHEN 1 THEN 'repair'
        WHEN 2 THEN 'inspection'
        ELSE 'recall'
    END,
    CASE number % 5
        WHEN 0 THEN 'battery_health'
        WHEN 1 THEN 'charging_system'
        WHEN 2 THEN 'thermal_management'
        WHEN 3 THEN 'software_update'
        ELSE 'scheduled_service'
    END,
    vehicle_number * 1425.0 + number * 55.0,
    number % 3 <> 0,
    number % 6 = 0,
    CASE
        WHEN visit_status = 'completed' AND number % 3 = 0 THEN 0
        WHEN visit_status = 'completed' THEN 850000 + number * 27500
        ELSE NULL
    END,
    CASE WHEN visit_status = 'completed' THEN 'VND' ELSE NULL END,
    CASE WHEN visit_status = 'completed' THEN 3 + number % 3 ELSE NULL END,
    CASE WHEN number % 9 = 0 THEN 'critical' WHEN number % 4 = 0 THEN 'high' ELSE 'normal' END,
    CASE number % 4 WHEN 0 THEN 'BMS_TEMP' WHEN 1 THEN 'CHG_PORT' WHEN 2 THEN 'TELEM_FW' ELSE 'SCHEDULED' END,
    CASE WHEN visit_status = 'completed' THEN 'RES-' || to_char(200 + number, 'FM000') END,
    'TEAM-ENT-' || to_char(((number - 1) % 4) + 1, 'FM00'),
    CASE WHEN visit_status = 'completed' THEN 120000 + number * 6500 END,
    CASE WHEN visit_status = 'completed' THEN 'VND' END,
    COALESCE(
        CASE WHEN visit_status IN ('completed', 'cancelled')
            THEN opened_at + CASE WHEN visit_status = 'completed' THEN INTERVAL '5 hours' ELSE INTERVAL '1 hour' END
        END,
        opened_at
    ) + INTERVAL '10 minutes'
FROM service_rows;

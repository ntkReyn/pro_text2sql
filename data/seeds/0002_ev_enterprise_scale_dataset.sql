-- Scaled synthetic enterprise dataset.
--
-- This seed intentionally uses a larger, relationally derived volume instead
-- of repeating the same row. New rows are isolated in the SCL namespace and
-- can coexist with both the LAB fixture and the smaller ENT dataset.
--
-- Rows added by this seed:
--   customers 100, vehicles 125, battery snapshots 275,
--   charging stations 100, charging sessions 300, service visits 160.
--
-- The fact-table volumes are larger because they represent history/events:
-- every non-inventory vehicle has battery history, charging history, and
-- service history; the first vehicles intentionally have additional events.

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
    'CUS-SCL-' || to_char(number, 'FM000'),
    'CRM-SCL-' || to_char(number, 'FM000'),
    CASE
        WHEN number % 10 = 0 THEN 'fleet'
        WHEN number % 4 = 0 THEN 'corporate'
        ELSE 'individual'
    END,
    CASE
        WHEN number % 10 = 0 THEN 'fleet'
        WHEN number % 3 = 0 OR number % 4 = 0 THEN 'premium'
        ELSE 'standard'
    END,
    CASE
        WHEN number % 10 = 0 OR number % 4 = 0 THEN NULL
        ELSE (ARRAY['18_24', '25_34', '35_44', '45_54', '55_plus'])[(number - 1) % 5 + 1]
    END,
    (ARRAY['NORTH', 'CENTRAL', 'SOUTH'])[(number - 1) % 3 + 1],
    CASE WHEN number % 6 = 0 THEN 'en' ELSE 'vi' END,
    date '2022-01-01' + number * 11,
    CASE WHEN number IN (97, 98, 99, 100) THEN 'inactive' ELSE 'active' END,
    number % 7 <> 0,
    'VN',
    (ARRAY['direct', 'dealer', 'fleet_sales', 'partner', 'online'])[(number - 1) % 5 + 1],
    CASE WHEN number % 7 <> 0 THEN timestamptz '2026-08-01 01:00:00+00' + number * INTERVAL '2 hours' END,
    timestamptz '2026-08-15 01:00:00+00' + number * INTERVAL '1 hour',
    (date '2022-01-01' + number * 11)::timestamptz,
    timestamptz '2026-08-15 01:00:00+00' + number * INTERVAL '1 hour'
FROM generate_series(1, 100) AS series(number);

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
    'VEH-SCL-' || to_char(number, 'FM000'),
    CASE
        WHEN number <= 100 THEN 'CUS-SCL-' || to_char(number, 'FM000')
        WHEN number <= 115 THEN 'CUS-SCL-' || to_char(((number - 101) % 15) + 1, 'FM000')
        ELSE NULL
    END,
    'ASSET-SCL-' || to_char(number, 'FM000'),
    'SYN-' || md5('vehicle-scl-' || number::text),
    (ARRAY['VF5', 'VF6', 'VF7', 'VF8', 'VF9'])[(number - 1) % 5 + 1],
    2022 + (number % 5),
    date '2022-01-01' + number * 7,
    CASE WHEN number > 115 THEN NULL ELSE date '2022-01-01' + number * 7 + 30 END,
    (ARRAY[37.20, 59.60, 75.30, 87.70, 123.00])[(number - 1) % 5 + 1],
    CASE
        WHEN number > 115 THEN 'inventory'
        WHEN number % 13 = 0 THEN 'in_service'
        WHEN number % 17 = 0 THEN 'inactive'
        ELSE 'active'
    END,
    'v' || (1 + number % 4)::text || '.' || (number % 10)::text || '.0',
    CASE WHEN number > 115 THEN NULL ELSE date '2022-01-01' + number * 7 + 30 END,
    CASE WHEN number > 115 THEN NULL ELSE date '2022-01-01' + number * 7 + 30 + 1460 END,
    CASE
        WHEN number > 115 THEN 'unknown'
        WHEN number % 19 = 0 THEN 'offline'
        WHEN number % 7 = 0 THEN 'degraded'
        ELSE 'online'
    END,
    timestamptz '2026-08-20 01:00:00+00' + number * INTERVAL '30 minutes'
FROM generate_series(1, 125) AS series(number);

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
    'BAT-SCL-' || to_char(vehicle_number, 'FM000') || '-' || observation_number,
    'VEH-SCL-' || to_char(vehicle_number, 'FM000'),
    'PACK-SCL-' || to_char(vehicle_number, 'FM000') ||
        CASE WHEN vehicle_number % 23 = 0 AND observation_number = 3 THEN '-R2' ELSE '-R1' END,
    timestamptz '2025-10-01 06:00:00+00'
        + vehicle_number * INTERVAL '1 day'
        + (observation_number - 1) * INTERVAL '90 days',
    (12 + ((vehicle_number * 17 + observation_number * 11) % 82))::numeric,
    round((CASE
        WHEN vehicle_number % 17 = 0 THEN 79.20
        ELSE 99.00 - (vehicle_number % 30) * 0.30
    END - (observation_number - 1) * 1.10)::numeric, 2),
    round((ARRAY[37.20, 59.60, 75.30, 87.70, 123.00])[(vehicle_number - 1) % 5 + 1]
        * (CASE
            WHEN vehicle_number % 17 = 0 THEN 79.20
            ELSE 99.00 - (vehicle_number % 30) * 0.30
        END - (observation_number - 1) * 1.10) / 100, 2),
    30 + vehicle_number * 8 + observation_number * 10,
    round((22 + ((vehicle_number * 5 + observation_number * 3) % 20))::numeric, 2),
    vehicle_number * 980.0 + observation_number * 240.0,
    CASE WHEN vehicle_number % 19 = 0 AND observation_number = 2 THEN 'estimated' ELSE 'validated' END,
    CASE WHEN observation_number = 1 THEN 'bms' ELSE 'telemetry' END,
    round((0.55 + (vehicle_number % 20) * 0.05)::numeric, 3),
    timestamptz '2025-10-01 06:10:00+00'
        + vehicle_number * INTERVAL '1 day'
        + (observation_number - 1) * INTERVAL '90 days'
FROM generate_series(1, 125) AS vehicles(vehicle_number)
CROSS JOIN LATERAL generate_series(
    1,
    CASE WHEN vehicles.vehicle_number <= 25 THEN 3 ELSE 2 END
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
SELECT
    'STN-SCL-' || to_char(number, 'FM000'),
    'STATION-SCL-' || to_char(number, 'FM000'),
    'Synthetic Network Station ' || to_char(number, 'FM000'),
    'OP-SCL-' || to_char(((number - 1) % 8) + 1, 'FM00'),
    CASE
        WHEN number % 10 = 0 THEN 'home'
        WHEN number % 4 = 0 THEN 'workplace'
        WHEN number % 3 = 0 THEN 'dealer'
        ELSE 'public'
    END,
    (ARRAY['NORTH', 'CENTRAL', 'SOUTH'])[(number - 1) % 3 + 1],
    (ARRAY['Ha Noi', 'Bac Ninh', 'Da Nang', 'Quang Nam', 'Ho Chi Minh City', 'Binh Duong'])[(number - 1) % 6 + 1],
    (ARRAY['Ha Noi', 'Bac Ninh', 'Da Nang', 'Hoi An', 'Ho Chi Minh City', 'Thu Dau Mot'])[(number - 1) % 6 + 1],
    CASE WHEN number % 5 = 0 THEN 'AC_TYPE2' ELSE 'DC_CCS2' END,
    CASE WHEN number % 5 = 0 THEN 22.00 ELSE 60.00 + (number % 8) * 30.00 END,
    CASE WHEN number % 10 = 0 THEN 1 ELSE 4 + (number % 17) END,
    CASE
        WHEN number % 29 = 0 THEN 'inactive'
        WHEN number % 17 = 0 THEN 'maintenance'
        ELSE 'operational'
    END,
    CASE
        WHEN number % 29 = 0 THEN 'offline'
        WHEN number % 17 = 0 THEN 'degraded'
        ELSE 'online'
    END,
    date '2024-01-01' + number * 3,
    CASE WHEN number % 29 = 0 THEN NULL ELSE timestamptz '2026-08-31 01:00:00+00' + number * INTERVAL '10 minutes' END,
    timestamptz '2026-09-01 01:00:00+00' + number * INTERVAL '15 minutes'
FROM generate_series(1, 100) AS series(number);

WITH session_rows AS (
    SELECT
        number,
        ((number - 1) % 115) + 1 AS vehicle_number,
        ((number - 1) % 100) + 1 AS station_number,
        CASE
            WHEN number % 10 IN (1, 2, 3, 4, 5, 6, 0) THEN 'completed'
            WHEN number % 10 = 7 THEN 'failed'
            WHEN number % 10 = 8 THEN 'cancelled'
            ELSE 'in_progress'
        END AS session_status,
        timestamptz '2025-10-15 02:00:00+00' + number * INTERVAL '1 day' AS started_at,
        (10 + (number * 9 % 50))::numeric AS start_soc_pct
    FROM generate_series(1, 300) AS series(number)
), calculated AS (
    SELECT
        session_rows.*,
        CASE WHEN session_status IN ('completed', 'failed', 'cancelled')
            THEN started_at + CASE
                WHEN session_status = 'completed' THEN INTERVAL '38 minutes'
                WHEN session_status = 'failed' THEN INTERVAL '6 minutes'
                ELSE INTERVAL '2 minutes'
            END
        END AS ended_at,
        CASE WHEN session_status = 'completed'
            THEN start_soc_pct + (24 + number % 4 * 5)
            WHEN session_status = 'failed' THEN start_soc_pct
        END AS end_soc_pct,
        CASE WHEN session_status = 'completed' THEN round((18 + number % 7 * 5)::numeric, 3)
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
    'CHG-SCL-' || to_char(number, 'FM000'),
    'SESSION-SCL-' || to_char(number, 'FM000'),
    'VEH-SCL-' || to_char(vehicle_number, 'FM000'),
    'STN-SCL-' || to_char(station_number, 'FM000'),
    started_at,
    ended_at,
    session_status,
    start_soc_pct,
    end_soc_pct,
    energy_delivered_kwh,
    CASE WHEN session_status = 'cancelled' THEN NULL ELSE 20 + number % 9 * 10 END,
    CASE
        WHEN session_status <> 'completed' THEN 'not_applicable'
        WHEN number % 3 = 1 THEN 'billed'
        WHEN number % 3 = 2 THEN 'free'
        ELSE 'unknown'
    END,
    CASE
        WHEN session_status = 'completed' AND number % 3 = 1 THEN round(energy_delivered_kwh * 4500, 2)
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
    'CON-' || to_char(((number - 1) % 20) + 1, 'FM00'),
    'fw-' || (2 + number % 3)::text || '.' || (number % 10)::text,
    CASE WHEN session_status = 'failed' THEN 'E-' || to_char(300 + number, 'FM000') ELSE NULL END,
    number * 50.000,
    CASE WHEN session_status IN ('completed', 'failed') THEN number * 50.000 + energy_delivered_kwh END,
    CASE WHEN session_status = 'completed' AND number % 3 = 1 THEN 'PAY-SCL-' || to_char(number, 'FM000') END,
    CASE WHEN number % 23 = 0 THEN 'estimated' ELSE 'validated' END,
    COALESCE(ended_at, started_at) + INTERVAL '5 minutes'
FROM calculated;

WITH service_rows AS (
    SELECT
        number,
        ((number - 1) % 115) + 1 AS vehicle_number,
        CASE
            WHEN number % 10 = 0 THEN 'cancelled'
            WHEN number % 10 = 1 THEN 'scheduled'
            WHEN number % 10 = 2 THEN 'in_progress'
            ELSE 'completed'
        END AS visit_status,
        timestamptz '2025-11-01 03:00:00+00' + number * INTERVAL '1 day' AS opened_at
    FROM generate_series(1, 160) AS series(number)
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
    'SRV-SCL-' || to_char(number, 'FM000'),
    'WO-SCL-' || to_char(number, 'FM000'),
    'VEH-SCL-' || to_char(vehicle_number, 'FM000'),
    'SC-SCL-' || to_char(((vehicle_number - 1) % 12) + 1, 'FM00'),
    opened_at,
    CASE WHEN visit_status IN ('completed', 'cancelled')
        THEN opened_at + CASE WHEN visit_status = 'completed' THEN INTERVAL '6 hours' ELSE INTERVAL '1 hour' END
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
    vehicle_number * 1180.0 + number * 62.0,
    number % 3 <> 0,
    number % 7 = 0,
    CASE
        WHEN visit_status <> 'completed' THEN NULL
        WHEN number % 3 = 0 THEN 0
        ELSE 700000 + number * 18500
    END,
    CASE WHEN visit_status = 'completed' THEN 'VND' ELSE NULL END,
    CASE WHEN visit_status = 'completed' THEN 3 + number % 3 ELSE NULL END,
    CASE WHEN number % 23 = 0 THEN 'critical' WHEN number % 5 = 0 THEN 'high' ELSE 'normal' END,
    CASE number % 4 WHEN 0 THEN 'BMS_TEMP' WHEN 1 THEN 'CHG_PORT' WHEN 2 THEN 'TELEM_FW' ELSE 'SCHEDULED' END,
    CASE WHEN visit_status = 'completed' THEN 'RES-' || to_char(500 + number, 'FM000') END,
    'TEAM-SCL-' || to_char(((number - 1) % 12) + 1, 'FM00'),
    CASE WHEN visit_status = 'completed' THEN 90000 + number * 4200 END,
    CASE WHEN visit_status = 'completed' THEN 'VND' END,
    COALESCE(
        CASE WHEN visit_status IN ('completed', 'cancelled')
            THEN opened_at + CASE WHEN visit_status = 'completed' THEN INTERVAL '6 hours' ELSE INTERVAL '1 hour' END
        END,
        opened_at
    ) + INTERVAL '10 minutes'
FROM service_rows;

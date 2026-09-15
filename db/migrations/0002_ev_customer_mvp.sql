CREATE TABLE analytics.dim_customer (
    customer_id text PRIMARY KEY,
    customer_type text NOT NULL
        CHECK (customer_type IN ('individual', 'corporate', 'fleet')),
    customer_segment text NOT NULL
        CHECK (customer_segment IN ('standard', 'premium', 'fleet')),
    age_band text
        CHECK (age_band IS NULL OR age_band IN ('18_24', '25_34', '35_44', '45_54', '55_plus')),
    home_region_code text NOT NULL,
    preferred_language text NOT NULL DEFAULT 'vi'
        CHECK (preferred_language IN ('vi', 'en')),
    joined_on date NOT NULL,
    customer_status text NOT NULL
        CHECK (customer_status IN ('active', 'inactive')),
    analytics_consent boolean NOT NULL DEFAULT false,
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE analytics.dim_customer IS
    'Synthetic MVP customer dimension. Grain: one current row per customer. It contains no direct personal identifiers.';
COMMENT ON COLUMN analytics.dim_customer.customer_id IS
    'Stable synthetic customer key; never a real customer identifier.';
COMMENT ON COLUMN analytics.dim_customer.analytics_consent IS
    'Synthetic consent flag for testing access and governance behavior; not a legal consent record.';

CREATE TABLE analytics.dim_vehicle (
    vehicle_id text PRIMARY KEY,
    current_customer_id text REFERENCES analytics.dim_customer (customer_id),
    vehicle_model_code text NOT NULL,
    model_year smallint NOT NULL CHECK (model_year BETWEEN 2020 AND 2100),
    manufactured_on date NOT NULL,
    delivered_on date,
    battery_nominal_capacity_kwh numeric(7, 2) NOT NULL
        CHECK (battery_nominal_capacity_kwh > 0),
    current_status text NOT NULL
        CHECK (current_status IN ('inventory', 'active', 'in_service', 'inactive')),
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT dim_vehicle_delivery_date_check
        CHECK (delivered_on IS NULL OR delivered_on >= manufactured_on),
    CONSTRAINT dim_vehicle_active_owner_check
        CHECK (current_status <> 'active' OR current_customer_id IS NOT NULL)
);

COMMENT ON TABLE analytics.dim_vehicle IS
    'Synthetic MVP vehicle dimension. Grain: one current row per vehicle. current_customer_id represents current ownership only.';
COMMENT ON COLUMN analytics.dim_vehicle.vehicle_id IS
    'Stable synthetic vehicle key; never a real VIN.';

CREATE TABLE analytics.fact_battery_health_snapshot (
    battery_snapshot_id text PRIMARY KEY,
    vehicle_id text NOT NULL REFERENCES analytics.dim_vehicle (vehicle_id),
    battery_pack_key text NOT NULL,
    observed_at timestamptz NOT NULL,
    state_of_charge_pct numeric(5, 2) NOT NULL
        CHECK (state_of_charge_pct BETWEEN 0 AND 100),
    state_of_health_pct numeric(5, 2) NOT NULL
        CHECK (state_of_health_pct BETWEEN 0 AND 100),
    usable_capacity_kwh numeric(7, 2) NOT NULL CHECK (usable_capacity_kwh > 0),
    cycle_count integer NOT NULL CHECK (cycle_count >= 0),
    pack_temperature_c numeric(5, 2)
        CHECK (pack_temperature_c IS NULL OR pack_temperature_c BETWEEN -40 AND 100),
    odometer_km numeric(12, 1) NOT NULL CHECK (odometer_km >= 0),
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT battery_snapshot_vehicle_time_uk UNIQUE (vehicle_id, observed_at)
);

COMMENT ON TABLE analytics.fact_battery_health_snapshot IS
    'Grain: one validated battery-health observation for one vehicle at one event timestamp.';
COMMENT ON COLUMN analytics.fact_battery_health_snapshot.battery_pack_key IS
    'Synthetic pack identifier that permits battery replacement history without storing a real serial number.';

CREATE TABLE analytics.dim_charging_station (
    charging_station_id text PRIMARY KEY,
    station_name text NOT NULL,
    operator_code text NOT NULL,
    station_scope text NOT NULL
        CHECK (station_scope IN ('public', 'dealer', 'workplace', 'home')),
    region_code text NOT NULL,
    province_name text NOT NULL,
    primary_connector_type text NOT NULL
        CHECK (primary_connector_type IN ('AC_TYPE2', 'DC_CCS2')),
    maximum_power_kw numeric(7, 2) NOT NULL CHECK (maximum_power_kw > 0),
    charging_port_count smallint NOT NULL CHECK (charging_port_count > 0),
    operational_status text NOT NULL
        CHECK (operational_status IN ('operational', 'maintenance', 'inactive')),
    commissioned_on date NOT NULL,
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE analytics.dim_charging_station IS
    'Synthetic MVP charging-station dimension. Grain: one current row per physical charging site.';
COMMENT ON COLUMN analytics.dim_charging_station.region_code IS
    'Coarse synthetic region used instead of precise GPS coordinates.';

CREATE TABLE analytics.fact_charging_session (
    charging_session_id text PRIMARY KEY,
    vehicle_id text NOT NULL REFERENCES analytics.dim_vehicle (vehicle_id),
    charging_station_id text NOT NULL
        REFERENCES analytics.dim_charging_station (charging_station_id),
    started_at timestamptz NOT NULL,
    ended_at timestamptz,
    session_status text NOT NULL
        CHECK (session_status IN ('completed', 'failed', 'cancelled', 'in_progress')),
    start_soc_pct numeric(5, 2) NOT NULL CHECK (start_soc_pct BETWEEN 0 AND 100),
    end_soc_pct numeric(5, 2) CHECK (end_soc_pct BETWEEN 0 AND 100),
    energy_delivered_kwh numeric(8, 3) NOT NULL DEFAULT 0
        CHECK (energy_delivered_kwh >= 0),
    peak_power_kw numeric(7, 2) CHECK (peak_power_kw IS NULL OR peak_power_kw >= 0),
    billing_status text NOT NULL
        CHECK (billing_status IN ('billed', 'free', 'unknown', 'not_applicable')),
    cost_amount numeric(12, 2) CHECK (cost_amount IS NULL OR cost_amount >= 0),
    currency_code character(3),
    stop_reason text,
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT charging_session_time_check
        CHECK (ended_at IS NULL OR ended_at > started_at),
    CONSTRAINT charging_session_soc_check
        CHECK (end_soc_pct IS NULL OR end_soc_pct >= start_soc_pct),
    CONSTRAINT charging_session_completed_check
        CHECK (
            session_status <> 'completed'
            OR (ended_at IS NOT NULL AND end_soc_pct IS NOT NULL AND energy_delivered_kwh > 0)
        ),
    CONSTRAINT charging_session_in_progress_check
        CHECK (session_status <> 'in_progress' OR ended_at IS NULL),
    CONSTRAINT charging_session_cost_currency_check
        CHECK (
            (cost_amount IS NULL AND currency_code IS NULL)
            OR (cost_amount IS NOT NULL AND currency_code IS NOT NULL)
        ),
    CONSTRAINT charging_session_billed_check
        CHECK (billing_status <> 'billed' OR cost_amount IS NOT NULL),
    CONSTRAINT charging_session_free_check
        CHECK (billing_status <> 'free' OR cost_amount = 0)
);

COMMENT ON TABLE analytics.fact_charging_session IS
    'Grain: one charging attempt by one vehicle at one station, including failed and cancelled attempts.';
COMMENT ON COLUMN analytics.fact_charging_session.started_at IS
    'Business event time used for time-range analytics; ingested_at is processing time.';

CREATE TABLE analytics.fact_service_visit (
    service_visit_id text PRIMARY KEY,
    vehicle_id text NOT NULL REFERENCES analytics.dim_vehicle (vehicle_id),
    service_center_code text NOT NULL,
    opened_at timestamptz NOT NULL,
    completed_at timestamptz,
    visit_status text NOT NULL
        CHECK (visit_status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    visit_type text NOT NULL
        CHECK (visit_type IN ('maintenance', 'repair', 'recall', 'inspection')),
    issue_category text NOT NULL,
    odometer_km numeric(12, 1) NOT NULL CHECK (odometer_km >= 0),
    warranty_covered boolean NOT NULL,
    is_repeat_issue boolean NOT NULL DEFAULT false,
    customer_paid_amount numeric(12, 2)
        CHECK (customer_paid_amount IS NULL OR customer_paid_amount >= 0),
    currency_code character(3),
    satisfaction_score smallint
        CHECK (satisfaction_score IS NULL OR satisfaction_score BETWEEN 1 AND 5),
    source_updated_at timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT service_visit_time_check
        CHECK (completed_at IS NULL OR completed_at >= opened_at),
    CONSTRAINT service_visit_completed_check
        CHECK (visit_status <> 'completed' OR completed_at IS NOT NULL),
    CONSTRAINT service_visit_cost_currency_check
        CHECK (
            (customer_paid_amount IS NULL AND currency_code IS NULL)
            OR (customer_paid_amount IS NOT NULL AND currency_code IS NOT NULL)
        )
);

COMMENT ON TABLE analytics.fact_service_visit IS
    'Grain: one service-center visit for one vehicle, including scheduled and cancelled visits.';

CREATE INDEX dim_vehicle_customer_idx
    ON analytics.dim_vehicle (current_customer_id);
CREATE INDEX battery_snapshot_vehicle_time_idx
    ON analytics.fact_battery_health_snapshot (vehicle_id, observed_at DESC);
CREATE INDEX battery_snapshot_soh_idx
    ON analytics.fact_battery_health_snapshot (state_of_health_pct);
CREATE INDEX charging_station_region_idx
    ON analytics.dim_charging_station (region_code);
CREATE INDEX charging_session_vehicle_time_idx
    ON analytics.fact_charging_session (vehicle_id, started_at DESC);
CREATE INDEX charging_session_station_time_idx
    ON analytics.fact_charging_session (charging_station_id, started_at DESC);
CREATE INDEX charging_session_status_time_idx
    ON analytics.fact_charging_session (session_status, started_at DESC);
CREATE INDEX service_visit_vehicle_time_idx
    ON analytics.fact_service_visit (vehicle_id, opened_at DESC);
CREATE INDEX service_visit_status_time_idx
    ON analytics.fact_service_visit (visit_status, opened_at DESC);

CREATE VIEW analytics.customer_vehicle_overview_v1 AS
WITH latest_battery AS (
    SELECT DISTINCT ON (snapshot.vehicle_id)
        snapshot.vehicle_id,
        snapshot.battery_pack_key,
        snapshot.observed_at AS battery_observed_at,
        snapshot.state_of_charge_pct,
        snapshot.state_of_health_pct,
        snapshot.usable_capacity_kwh,
        snapshot.cycle_count,
        snapshot.odometer_km
    FROM analytics.fact_battery_health_snapshot AS snapshot
    ORDER BY snapshot.vehicle_id, snapshot.observed_at DESC
),
charging_summary AS (
    SELECT
        session.vehicle_id,
        COUNT(*) AS charging_attempt_count,
        COUNT(*) FILTER (WHERE session.session_status = 'completed') AS completed_charging_session_count,
        COUNT(*) FILTER (WHERE session.session_status = 'failed') AS failed_charging_session_count,
        COALESCE(
            SUM(session.energy_delivered_kwh) FILTER (WHERE session.session_status = 'completed'),
            0
        ) AS completed_energy_delivered_kwh,
        MAX(session.started_at) AS latest_charging_started_at
    FROM analytics.fact_charging_session AS session
    GROUP BY session.vehicle_id
),
service_summary AS (
    SELECT
        visit.vehicle_id,
        COUNT(*) AS service_visit_count,
        COUNT(*) FILTER (WHERE visit.visit_status = 'completed') AS completed_service_visit_count,
        COUNT(*) FILTER (
            WHERE visit.visit_status = 'completed' AND visit.is_repeat_issue
        ) AS repeated_issue_visit_count,
        MAX(visit.opened_at) AS latest_service_opened_at
    FROM analytics.fact_service_visit AS visit
    GROUP BY visit.vehicle_id
)
SELECT
    vehicle.vehicle_id,
    vehicle.vehicle_model_code,
    vehicle.model_year,
    vehicle.delivered_on,
    vehicle.battery_nominal_capacity_kwh,
    vehicle.current_status AS vehicle_status,
    customer.customer_id,
    customer.customer_type,
    customer.customer_segment,
    customer.age_band,
    customer.home_region_code,
    customer.joined_on,
    customer.customer_status,
    customer.analytics_consent,
    battery.battery_pack_key,
    battery.battery_observed_at,
    battery.state_of_charge_pct,
    battery.state_of_health_pct,
    battery.usable_capacity_kwh,
    battery.cycle_count,
    battery.odometer_km,
    COALESCE(charging.charging_attempt_count, 0) AS charging_attempt_count,
    COALESCE(charging.completed_charging_session_count, 0) AS completed_charging_session_count,
    COALESCE(charging.failed_charging_session_count, 0) AS failed_charging_session_count,
    COALESCE(charging.completed_energy_delivered_kwh, 0) AS completed_energy_delivered_kwh,
    charging.latest_charging_started_at,
    COALESCE(service.service_visit_count, 0) AS service_visit_count,
    COALESCE(service.completed_service_visit_count, 0) AS completed_service_visit_count,
    COALESCE(service.repeated_issue_visit_count, 0) AS repeated_issue_visit_count,
    service.latest_service_opened_at,
    GREATEST(
        vehicle.source_updated_at,
        COALESCE(customer.source_updated_at, '-infinity'::timestamptz)
    ) AS source_updated_at,
    now() AS model_built_at
FROM analytics.dim_vehicle AS vehicle
LEFT JOIN analytics.dim_customer AS customer
    ON customer.customer_id = vehicle.current_customer_id
LEFT JOIN latest_battery AS battery
    ON battery.vehicle_id = vehicle.vehicle_id
LEFT JOIN charging_summary AS charging
    ON charging.vehicle_id = vehicle.vehicle_id
LEFT JOIN service_summary AS service
    ON service.vehicle_id = vehicle.vehicle_id;

COMMENT ON VIEW analytics.customer_vehicle_overview_v1 IS
    'Semantic-friendly mart. Grain: one current vehicle, with facts aggregated independently before joining to prevent fan-out.';

CREATE VIEW analytics.charging_session_analytics_v1 AS
SELECT
    session.charging_session_id,
    session.started_at,
    session.ended_at,
    CASE
        WHEN session.ended_at IS NULL THEN NULL
        ELSE EXTRACT(EPOCH FROM (session.ended_at - session.started_at)) / 60.0
    END AS duration_minutes,
    session.session_status,
    session.start_soc_pct,
    session.end_soc_pct,
    session.energy_delivered_kwh,
    session.peak_power_kw,
    session.billing_status,
    session.cost_amount,
    session.currency_code,
    session.stop_reason,
    vehicle.vehicle_id,
    vehicle.vehicle_model_code,
    vehicle.model_year,
    customer.customer_id,
    customer.customer_segment,
    customer.home_region_code AS customer_region_code,
    station.charging_station_id,
    station.station_name,
    station.station_scope,
    station.region_code AS station_region_code,
    station.province_name,
    station.primary_connector_type,
    station.maximum_power_kw,
    GREATEST(
        session.source_updated_at,
        vehicle.source_updated_at,
        station.source_updated_at,
        COALESCE(customer.source_updated_at, '-infinity'::timestamptz)
    ) AS source_updated_at,
    now() AS model_built_at
FROM analytics.fact_charging_session AS session
INNER JOIN analytics.dim_vehicle AS vehicle
    ON vehicle.vehicle_id = session.vehicle_id
INNER JOIN analytics.dim_charging_station AS station
    ON station.charging_station_id = session.charging_station_id
LEFT JOIN analytics.dim_customer AS customer
    ON customer.customer_id = vehicle.current_customer_id;

COMMENT ON VIEW analytics.charging_session_analytics_v1 IS
    'Semantic-friendly mart. Grain: one charging attempt, enriched with current vehicle, customer and station dimensions.';

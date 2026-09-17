-- Enterprise extensions for the six-table EV analytics model.
--
-- These fields stay in the governed source layer. The Wren semantic marts
-- intentionally expose only business-safe analytical fields, not operational
-- identifiers such as asset tokens, payment references, or technician codes.

ALTER TABLE analytics.dim_customer
    ADD COLUMN customer_reference text,
    ADD COLUMN country_code character(2) NOT NULL DEFAULT 'VN',
    ADD COLUMN acquisition_channel text NOT NULL DEFAULT 'direct'
        CHECK (acquisition_channel IN ('direct', 'dealer', 'fleet_sales', 'partner', 'online')),
    ADD COLUMN consent_updated_at timestamptz,
    ADD COLUMN created_at timestamptz NOT NULL DEFAULT now(),
    ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();

UPDATE analytics.dim_customer
SET customer_reference = 'CRM-' || upper(regexp_replace(customer_id, '[^A-Za-z0-9]+', '-', 'g'))
WHERE customer_reference IS NULL;

ALTER TABLE analytics.dim_customer
    ALTER COLUMN customer_reference SET NOT NULL,
    ADD CONSTRAINT dim_customer_customer_reference_uk UNIQUE (customer_reference),
    ADD CONSTRAINT dim_customer_audit_time_check CHECK (updated_at >= created_at);

COMMENT ON COLUMN analytics.dim_customer.customer_reference IS
    'Synthetic CRM reference for integration tests; not a real account number.';
COMMENT ON COLUMN analytics.dim_customer.country_code IS
    'ISO-like two-letter operating-country code for the synthetic dataset.';

ALTER TABLE analytics.dim_vehicle
    ADD COLUMN vehicle_asset_tag text,
    ADD COLUMN vehicle_identity_token text,
    ADD COLUMN software_version text NOT NULL DEFAULT 'unknown',
    ADD COLUMN warranty_start_on date,
    ADD COLUMN warranty_end_on date,
    ADD COLUMN connectivity_status text NOT NULL DEFAULT 'unknown'
        CHECK (connectivity_status IN ('online', 'degraded', 'offline', 'unknown'));

UPDATE analytics.dim_vehicle
SET vehicle_asset_tag = 'ASSET-' || upper(regexp_replace(vehicle_id, '[^A-Za-z0-9]+', '-', 'g')),
    vehicle_identity_token = 'SYN-' || md5(vehicle_id),
    warranty_start_on = COALESCE(delivered_on, manufactured_on),
    warranty_end_on = (COALESCE(delivered_on, manufactured_on) + INTERVAL '4 years')::date
WHERE vehicle_asset_tag IS NULL;

ALTER TABLE analytics.dim_vehicle
    ALTER COLUMN vehicle_asset_tag SET NOT NULL,
    ALTER COLUMN vehicle_identity_token SET NOT NULL,
    ADD CONSTRAINT dim_vehicle_asset_tag_uk UNIQUE (vehicle_asset_tag),
    ADD CONSTRAINT dim_vehicle_identity_token_uk UNIQUE (vehicle_identity_token),
    ADD CONSTRAINT dim_vehicle_warranty_date_check
        CHECK (warranty_end_on IS NULL OR warranty_start_on IS NULL OR warranty_end_on >= warranty_start_on);

COMMENT ON COLUMN analytics.dim_vehicle.vehicle_identity_token IS
    'Synthetic one-way identity token; deliberately not a real VIN.';
COMMENT ON COLUMN analytics.dim_vehicle.connectivity_status IS
    'Latest telematics connectivity state used for operational monitoring.';

ALTER TABLE analytics.fact_battery_health_snapshot
    ADD COLUMN data_quality_status text NOT NULL DEFAULT 'validated'
        CHECK (data_quality_status IN ('validated', 'estimated', 'rejected')),
    ADD COLUMN measurement_source text NOT NULL DEFAULT 'bms'
        CHECK (measurement_source IN ('bms', 'telemetry', 'service')),
    ADD COLUMN degradation_rate_pct_per_1000_cycles numeric(7, 3)
        CHECK (degradation_rate_pct_per_1000_cycles IS NULL OR degradation_rate_pct_per_1000_cycles >= 0);

ALTER TABLE analytics.dim_charging_station
    ADD COLUMN station_external_ref text,
    ADD COLUMN city_name text NOT NULL DEFAULT 'Unknown',
    ADD COLUMN network_status text NOT NULL DEFAULT 'unknown'
        CHECK (network_status IN ('online', 'degraded', 'offline', 'unknown')),
    ADD COLUMN last_heartbeat_at timestamptz;

UPDATE analytics.dim_charging_station
SET station_external_ref = 'STATION-' || upper(regexp_replace(charging_station_id, '[^A-Za-z0-9]+', '-', 'g')),
    city_name = province_name
WHERE station_external_ref IS NULL;

ALTER TABLE analytics.dim_charging_station
    ALTER COLUMN station_external_ref SET NOT NULL,
    ADD CONSTRAINT dim_charging_station_external_ref_uk UNIQUE (station_external_ref);

COMMENT ON COLUMN analytics.dim_charging_station.station_external_ref IS
    'Synthetic external reference for charger-network integration.';

ALTER TABLE analytics.fact_charging_session
    ADD COLUMN session_reference text,
    ADD COLUMN connector_id text,
    ADD COLUMN firmware_version text NOT NULL DEFAULT 'unknown',
    ADD COLUMN error_code text,
    ADD COLUMN meter_start_kwh numeric(12, 3),
    ADD COLUMN meter_end_kwh numeric(12, 3),
    ADD COLUMN payment_transaction_ref text,
    ADD COLUMN data_quality_status text NOT NULL DEFAULT 'validated'
        CHECK (data_quality_status IN ('validated', 'estimated', 'rejected'));

UPDATE analytics.fact_charging_session
SET session_reference = 'SESSION-' || upper(regexp_replace(charging_session_id, '[^A-Za-z0-9]+', '-', 'g'))
WHERE session_reference IS NULL;

ALTER TABLE analytics.fact_charging_session
    ALTER COLUMN session_reference SET NOT NULL,
    ADD CONSTRAINT fact_charging_session_reference_uk UNIQUE (session_reference),
    ADD CONSTRAINT charging_session_meter_check
        CHECK (meter_end_kwh IS NULL OR meter_start_kwh IS NULL OR meter_end_kwh >= meter_start_kwh);

COMMENT ON COLUMN analytics.fact_charging_session.payment_transaction_ref IS
    'Synthetic payment reference; no payment-provider secret or real transaction identifier.';

ALTER TABLE analytics.fact_service_visit
    ADD COLUMN work_order_number text,
    ADD COLUMN service_priority text NOT NULL DEFAULT 'normal'
        CHECK (service_priority IN ('low', 'normal', 'high', 'critical')),
    ADD COLUMN root_cause_code text,
    ADD COLUMN resolution_code text,
    ADD COLUMN technician_team_code text,
    ADD COLUMN parts_cost_amount numeric(12, 2)
        CHECK (parts_cost_amount IS NULL OR parts_cost_amount >= 0),
    ADD COLUMN parts_currency_code character(3),
    ADD CONSTRAINT service_parts_cost_currency_check
        CHECK (
            (parts_cost_amount IS NULL AND parts_currency_code IS NULL)
            OR (parts_cost_amount IS NOT NULL AND parts_currency_code IS NOT NULL)
        );

UPDATE analytics.fact_service_visit
SET work_order_number = 'WO-' || upper(regexp_replace(service_visit_id, '[^A-Za-z0-9]+', '-', 'g'))
WHERE work_order_number IS NULL;

ALTER TABLE analytics.fact_service_visit
    ALTER COLUMN work_order_number SET NOT NULL,
    ADD CONSTRAINT fact_service_visit_work_order_uk UNIQUE (work_order_number);

COMMENT ON COLUMN analytics.fact_service_visit.work_order_number IS
    'Synthetic service work-order reference for after-sales integration.';

CREATE INDEX dim_customer_region_status_idx
    ON analytics.dim_customer (home_region_code, customer_status);
CREATE INDEX dim_vehicle_status_connectivity_idx
    ON analytics.dim_vehicle (current_status, connectivity_status);
CREATE INDEX battery_snapshot_quality_time_idx
    ON analytics.fact_battery_health_snapshot (data_quality_status, observed_at DESC);
CREATE INDEX charging_station_network_status_idx
    ON analytics.dim_charging_station (network_status, operational_status);
CREATE INDEX charging_session_quality_time_idx
    ON analytics.fact_charging_session (data_quality_status, started_at DESC);
CREATE INDEX service_visit_priority_time_idx
    ON analytics.fact_service_visit (service_priority, opened_at DESC);

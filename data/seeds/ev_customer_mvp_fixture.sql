-- Entirely synthetic data for local development and Text-to-SQL evaluation.
-- IDs, names, locations and operational events do not represent real people,
-- vehicles, stations or internal business records.

INSERT INTO analytics.dim_customer (
    customer_id,
    customer_type,
    customer_segment,
    age_band,
    home_region_code,
    preferred_language,
    joined_on,
    customer_status,
    analytics_consent,
    source_updated_at
) VALUES
    ('CUS-LAB-001', 'individual', 'premium',  '35_44',   'NORTH',   'vi', '2025-01-15', 'active',   true,  '2026-09-14T00:00:00Z'),
    ('CUS-LAB-002', 'individual', 'standard', '25_34',   'NORTH',   'vi', '2025-03-04', 'active',   true,  '2026-09-14T00:00:00Z'),
    ('CUS-LAB-003', 'individual', 'standard', '45_54',   'CENTRAL', 'vi', '2025-04-22', 'active',   false, '2026-09-14T00:00:00Z'),
    ('CUS-LAB-004', 'corporate',  'premium',  NULL,      'SOUTH',   'en', '2025-06-10', 'active',   true,  '2026-09-14T00:00:00Z'),
    ('CUS-LAB-005', 'individual', 'standard', '55_plus', 'SOUTH',   'vi', '2024-11-08', 'active',   true,  '2026-09-14T00:00:00Z'),
    ('CUS-LAB-006', 'individual', 'standard', '18_24',   'CENTRAL', 'vi', '2026-01-19', 'inactive', false, '2026-09-14T00:00:00Z'),
    ('CUS-LAB-007', 'fleet',      'fleet',    NULL,      'SOUTH',   'vi', '2025-08-01', 'active',   true,  '2026-09-14T00:00:00Z'),
    ('CUS-LAB-008', 'individual', 'standard', '25_34',   'NORTH',   'vi', '2026-09-01', 'active',   true,  '2026-09-14T00:00:00Z');

INSERT INTO analytics.dim_vehicle (
    vehicle_id,
    current_customer_id,
    vehicle_model_code,
    model_year,
    manufactured_on,
    delivered_on,
    battery_nominal_capacity_kwh,
    current_status,
    source_updated_at
) VALUES
    ('VEH-LAB-001', 'CUS-LAB-001', 'VF8_LAB', 2025, '2025-01-05', '2025-02-01', 87.70, 'active',     '2026-09-14T00:00:00Z'),
    ('VEH-LAB-002', 'CUS-LAB-001', 'VF6_LAB', 2026, '2026-01-10', '2026-02-03', 59.60, 'active',     '2026-09-14T00:00:00Z'),
    ('VEH-LAB-003', 'CUS-LAB-002', 'VF7_LAB', 2025, '2025-02-11', '2025-03-15', 75.30, 'active',     '2026-09-14T00:00:00Z'),
    ('VEH-LAB-004', 'CUS-LAB-003', 'VF8_LAB', 2025, '2025-03-12', '2025-05-01', 87.70, 'in_service', '2026-09-14T00:00:00Z'),
    ('VEH-LAB-005', 'CUS-LAB-004', 'VF9_LAB', 2025, '2025-04-18', '2025-06-28', 123.00, 'active',    '2026-09-14T00:00:00Z'),
    ('VEH-LAB-006', 'CUS-LAB-005', 'VF7_LAB', 2024, '2024-09-20', '2024-12-01', 75.30, 'active',     '2026-09-14T00:00:00Z'),
    ('VEH-LAB-007', 'CUS-LAB-006', 'VF6_LAB', 2024, '2024-08-08', '2024-10-09', 59.60, 'inactive',   '2026-09-14T00:00:00Z'),
    ('VEH-LAB-008', 'CUS-LAB-007', 'VF8_LAB', 2026, '2026-01-20', '2026-02-20', 87.70, 'active',     '2026-09-14T00:00:00Z'),
    ('VEH-LAB-009', NULL,          'VF9_LAB', 2026, '2026-08-01', NULL,         123.00, 'inventory',  '2026-09-14T00:00:00Z');

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
    source_updated_at
) VALUES
    ('BAT-SNAP-001', 'VEH-LAB-001', 'PACK-LAB-A01', '2026-07-01T08:00:00+07:00', 72.10, 96.30, 84.45, 210, 35.20, 18240.0, '2026-07-01T01:00:05Z'),
    ('BAT-SNAP-002', 'VEH-LAB-001', 'PACK-LAB-A01', '2026-09-01T08:00:00+07:00', 63.40, 95.90, 84.10, 238, 34.80, 20560.0, '2026-09-01T01:00:05Z'),
    ('BAT-SNAP-003', 'VEH-LAB-002', 'PACK-LAB-A02', '2026-07-01T08:05:00+07:00', 44.00, 99.10, 59.06,  45, 33.10,  4320.0, '2026-07-01T01:05:05Z'),
    ('BAT-SNAP-004', 'VEH-LAB-002', 'PACK-LAB-A02', '2026-09-01T08:05:00+07:00', 81.20, 98.80, 58.88,  61, 34.50,  5980.0, '2026-09-01T01:05:05Z'),
    ('BAT-SNAP-005', 'VEH-LAB-003', 'PACK-LAB-A03', '2026-07-03T07:30:00+07:00', 35.60, 94.20, 70.93, 330, 36.90, 31200.0, '2026-07-03T00:30:05Z'),
    ('BAT-SNAP-006', 'VEH-LAB-003', 'PACK-LAB-A03', '2026-09-03T07:30:00+07:00', 29.80, 93.50, 70.41, 365, 37.20, 34150.0, '2026-09-03T00:30:05Z'),
    ('BAT-SNAP-007', 'VEH-LAB-004', 'PACK-LAB-A04', '2026-07-05T09:00:00+07:00', 58.20, 88.40, 77.53, 520, 41.00, 52200.0, '2026-07-05T02:00:05Z'),
    ('BAT-SNAP-008', 'VEH-LAB-004', 'PACK-LAB-A04', '2026-09-05T09:00:00+07:00', 49.10, 86.90, 76.21, 558, NULL,  55400.0, '2026-09-05T02:00:05Z'),
    ('BAT-SNAP-009', 'VEH-LAB-005', 'PACK-LAB-A05', '2026-07-10T10:00:00+07:00', 90.00, 97.70, 120.17, 125, 32.60, 11400.0, '2026-07-10T03:00:05Z'),
    ('BAT-SNAP-010', 'VEH-LAB-005', 'PACK-LAB-A05', '2026-09-10T10:00:00+07:00', 76.50, 97.30, 119.68, 143, 33.40, 13200.0, '2026-09-10T03:00:05Z'),
    ('BAT-SNAP-011', 'VEH-LAB-006', 'PACK-LAB-OLD6', '2026-07-12T11:00:00+07:00', 42.50, 77.80, 58.58, 760, 43.20, 78200.0, '2026-07-12T04:00:05Z'),
    ('BAT-SNAP-012', 'VEH-LAB-006', 'PACK-LAB-NEW6', '2026-09-12T11:00:00+07:00', 88.00, 99.80, 75.15,   4, 31.80, 78940.0, '2026-09-12T04:00:05Z'),
    ('BAT-SNAP-013', 'VEH-LAB-007', 'PACK-LAB-A07', '2026-07-15T13:00:00+07:00', 31.00, 79.30, 47.26, 810, 39.80, 84500.0, '2026-07-15T06:00:05Z'),
    ('BAT-SNAP-014', 'VEH-LAB-007', 'PACK-LAB-A07', '2026-09-13T13:00:00+07:00', 26.20, 78.50, 46.79, 835, 40.10, 86600.0, '2026-09-13T06:00:05Z'),
    ('BAT-SNAP-015', 'VEH-LAB-008', 'PACK-LAB-A08', '2026-07-20T14:00:00+07:00', 69.00, 99.40, 87.17,  80, 34.00,  7200.0, '2026-07-20T07:00:05Z'),
    ('BAT-SNAP-016', 'VEH-LAB-008', 'PACK-LAB-A08', '2026-09-14T14:00:00+07:00', 54.50, 99.00, 86.82, 102, 35.10,  9100.0, '2026-09-14T07:00:05Z');

INSERT INTO analytics.dim_charging_station (
    charging_station_id,
    station_name,
    operator_code,
    station_scope,
    region_code,
    province_name,
    primary_connector_type,
    maximum_power_kw,
    charging_port_count,
    operational_status,
    commissioned_on,
    source_updated_at
) VALUES
    ('STN-LAB-HN-01',   'Lab Station Ha Noi 01',   'OP-LAB-A', 'public',    'NORTH',   'Ha Noi',          'DC_CCS2', 150.00, 8, 'operational', '2025-01-01', '2026-09-14T00:00:00Z'),
    ('STN-LAB-HN-02',   'Lab Dealer Ha Noi',       'OP-LAB-A', 'dealer',    'NORTH',   'Ha Noi',          'DC_CCS2', 120.00, 4, 'maintenance', '2025-02-01', '2026-09-14T00:00:00Z'),
    ('STN-LAB-DN-01',   'Lab Station Da Nang 01',  'OP-LAB-A', 'public',    'CENTRAL', 'Da Nang',         'DC_CCS2',  60.00, 6, 'operational', '2025-03-01', '2026-09-14T00:00:00Z'),
    ('STN-LAB-HCM-01',  'Lab Station HCM 01',      'OP-LAB-B', 'public',    'SOUTH',   'Ho Chi Minh City', 'DC_CCS2', 250.00, 12, 'operational', '2025-01-15', '2026-09-14T00:00:00Z'),
    ('STN-LAB-HCM-02',  'Lab Workplace HCM',       'OP-LAB-B', 'workplace', 'SOUTH',   'Ho Chi Minh City', 'AC_TYPE2',  22.00, 10, 'operational', '2025-05-10', '2026-09-14T00:00:00Z'),
    ('STN-LAB-HOME-01', 'Lab Home Charger 01',     'OP-LAB-H', 'home',      'NORTH',   'Ha Noi',          'AC_TYPE2',  11.00, 1, 'operational', '2025-02-01', '2026-09-14T00:00:00Z');

INSERT INTO analytics.fact_charging_session (
    charging_session_id,
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
    source_updated_at
) VALUES
    ('CHG-LAB-001', 'VEH-LAB-001', 'STN-LAB-HOME-01', '2026-07-31T22:30:00+07:00', '2026-08-01T03:10:00+07:00', 'completed',   24.00, 90.00, 58.200, 10.80, 'free',           0, 'VND', 'target_soc',          '2026-07-31T20:10:05Z'),
    ('CHG-LAB-002', 'VEH-LAB-001', 'STN-LAB-HN-01',   '2026-08-15T08:00:00+07:00', '2026-08-15T08:31:00+07:00', 'completed',   18.00, 72.00, 47.300, 142.00, 'billed',    189200, 'VND', 'user_stop',           '2026-08-15T01:31:05Z'),
    ('CHG-LAB-003', 'VEH-LAB-002', 'STN-LAB-HN-02',   '2026-08-20T09:00:00+07:00', '2026-08-20T09:04:00+07:00', 'failed',      31.00, 32.00,  0.500,  12.00, 'not_applicable', NULL, NULL,  'station_fault',       '2026-08-20T02:04:05Z'),
    ('CHG-LAB-004', 'VEH-LAB-002', 'STN-LAB-HN-01',   '2026-08-31T23:50:00+07:00', '2026-09-01T00:24:00+07:00', 'completed',   22.00, 78.00, 34.000,  58.00, 'billed',    136000, 'VND', 'target_soc',          '2026-08-31T17:24:05Z'),
    ('CHG-LAB-005', 'VEH-LAB-003', 'STN-LAB-DN-01',   '2026-09-02T12:10:00+07:00', '2026-09-02T13:00:00+07:00', 'completed',   15.00, 70.00, 41.500,  57.00, 'billed',    166000, 'VND', 'user_stop',           '2026-09-02T06:00:05Z'),
    ('CHG-LAB-006', 'VEH-LAB-003', 'STN-LAB-DN-01',   '2026-09-06T15:00:00+07:00', '2026-09-06T15:01:00+07:00', 'cancelled',   63.00, NULL,   0.000,  NULL,  'not_applicable', NULL, NULL,  'user_cancelled',      '2026-09-06T08:01:05Z'),
    ('CHG-LAB-007', 'VEH-LAB-004', 'STN-LAB-DN-01',   '2026-09-07T10:00:00+07:00', '2026-09-07T10:45:00+07:00', 'completed',   20.00, 61.00, 36.400,  55.00, 'billed',    145600, 'VND', 'user_stop',           '2026-09-07T03:45:05Z'),
    ('CHG-LAB-008', 'VEH-LAB-005', 'STN-LAB-HCM-01',  '2026-09-08T07:00:00+07:00', '2026-09-08T07:38:00+07:00', 'completed',   12.00, 82.00, 86.000, 235.00, 'billed',    344000, 'VND', 'target_soc',          '2026-09-08T00:38:05Z'),
    ('CHG-LAB-009', 'VEH-LAB-005', 'STN-LAB-HCM-02',  '2026-09-09T18:00:00+07:00', '2026-09-09T21:10:00+07:00', 'completed',   45.00, 80.00, 43.000,  21.00, 'free',           0, 'VND', 'target_soc',          '2026-09-09T14:10:05Z'),
    ('CHG-LAB-010', 'VEH-LAB-006', 'STN-LAB-HCM-01',  '2026-07-15T06:30:00+07:00', '2026-07-15T06:55:00+07:00', 'completed',   10.00, 48.00, 28.000, 118.00, 'unknown',      NULL, NULL,  'vehicle_disconnect',  '2026-07-14T23:55:05Z'),
    ('CHG-LAB-011', 'VEH-LAB-006', 'STN-LAB-HCM-01',  '2026-09-12T15:00:00+07:00', '2026-09-12T15:30:00+07:00', 'completed',   30.00, 82.00, 39.000, 145.00, 'billed',    156000, 'VND', 'target_soc',          '2026-09-12T08:30:05Z'),
    ('CHG-LAB-012', 'VEH-LAB-007', 'STN-LAB-DN-01',   '2026-08-10T11:30:00+07:00', '2026-08-10T11:36:00+07:00', 'failed',      19.00, 20.00,  0.800,   8.00, 'not_applicable', NULL, NULL,  'vehicle_fault',       '2026-08-10T04:36:05Z'),
    ('CHG-LAB-013', 'VEH-LAB-008', 'STN-LAB-HCM-01',  '2026-09-13T16:00:00+07:00', '2026-09-13T16:29:00+07:00', 'completed',   25.00, 79.00, 47.400, 148.00, 'billed',    189600, 'VND', 'target_soc',          '2026-09-13T09:29:05Z'),
    ('CHG-LAB-014', 'VEH-LAB-008', 'STN-LAB-HCM-02',  '2026-09-14T20:00:00+07:00', NULL,                        'in_progress', 50.00, NULL,   8.200,  20.00, 'not_applicable', NULL, NULL,  'ongoing',             '2026-09-14T13:30:05Z'),
    ('CHG-LAB-015', 'VEH-LAB-001', 'STN-LAB-HN-01',   '2026-09-14T08:00:00+07:00', '2026-09-14T08:03:00+07:00', 'failed',      40.00, 40.00,  0.000,   0.00, 'not_applicable', NULL, NULL,  'payment_authorization','2026-09-14T01:03:05Z');

INSERT INTO analytics.fact_service_visit (
    service_visit_id,
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
    source_updated_at
) VALUES
    ('SRV-LAB-001', 'VEH-LAB-001', 'SC-LAB-HN-01',  '2026-06-10T08:00:00+07:00', '2026-06-10T15:00:00+07:00', 'completed',   'maintenance', 'scheduled_service', 17100.0, false, false, 1800000, 'VND', 5,    '2026-06-10T08:00:05Z'),
    ('SRV-LAB-002', 'VEH-LAB-002', 'SC-LAB-HN-01',  '2026-08-02T08:30:00+07:00', '2026-08-02T12:00:00+07:00', 'completed',   'repair',      'charging_system',    5100.0, true,  false,       0, 'VND', 4,    '2026-08-02T05:00:05Z'),
    ('SRV-LAB-003', 'VEH-LAB-002', 'SC-LAB-HN-01',  '2026-08-25T09:00:00+07:00', '2026-08-25T14:30:00+07:00', 'completed',   'repair',      'charging_system',    5700.0, true,  true,        0, 'VND', 3,    '2026-08-25T07:30:05Z'),
    ('SRV-LAB-004', 'VEH-LAB-003', 'SC-LAB-DN-01',  '2026-08-31T16:00:00+07:00', '2026-09-01T11:00:00+07:00', 'completed',   'inspection',  'battery_health',    33900.0, false, false,  600000, 'VND', 4,    '2026-09-01T04:00:05Z'),
    ('SRV-LAB-005', 'VEH-LAB-004', 'SC-LAB-DN-01',  '2026-09-05T08:00:00+07:00', NULL,                        'in_progress', 'repair',      'thermal_management',55400.0, true,  false,    NULL, NULL,  NULL, '2026-09-05T02:00:05Z'),
    ('SRV-LAB-006', 'VEH-LAB-005', 'SC-LAB-HCM-01', '2026-07-20T08:00:00+07:00', '2026-07-20T13:00:00+07:00', 'completed',   'maintenance', 'scheduled_service', 12000.0, false, false, 2400000, 'VND', 5,    '2026-07-20T06:00:05Z'),
    ('SRV-LAB-007', 'VEH-LAB-006', 'SC-LAB-HCM-01', '2026-08-14T08:00:00+07:00', '2026-08-15T17:00:00+07:00', 'completed',   'repair',      'battery_health',    78600.0, true,  false,       0, 'VND', 4,    '2026-08-15T10:00:05Z'),
    ('SRV-LAB-008', 'VEH-LAB-007', 'SC-LAB-DN-01',  '2026-08-21T10:00:00+07:00', '2026-08-21T10:00:00+07:00', 'cancelled',   'maintenance', 'scheduled_service', 85400.0, false, false,    NULL, NULL,  NULL, '2026-08-21T03:00:05Z'),
    ('SRV-LAB-009', 'VEH-LAB-008', 'SC-LAB-HCM-02', '2026-09-10T09:00:00+07:00', '2026-09-10T12:00:00+07:00', 'completed',   'recall',      'software_update',    8900.0, true,  false,       0, 'VND', 5,    '2026-09-10T05:00:05Z'),
    ('SRV-LAB-010', 'VEH-LAB-001', 'SC-LAB-HN-01',  '2026-09-20T08:00:00+07:00', NULL,                        'scheduled',   'inspection',  'battery_health',    20800.0, false, false,    NULL, NULL,  NULL, '2026-09-14T00:00:00Z');

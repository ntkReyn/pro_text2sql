# Canonical EV analytics metrics

This project is synthetic. Wren is the semantic SQL compiler and physical
mapping authority. The following governed formulas must not be redefined by the
SQL agent.

- `customer_count`: `COUNT(*)` on `customer_analytics_v1`.
- `vehicle_count`: `COUNT(*)` on `vehicle_analytics_v1`.
- `average_latest_battery_soh_pct`: `AVG(state_of_health_pct)` on the latest-snapshot mart.
- `battery_watch_vehicle_count`: `COUNT(*)` where `state_of_health_pct < 80`.
- `successful_charging_session_count`: `COUNT(*)` where status is completed and delivered energy is positive.
- `failed_charging_session_count`: `COUNT(*)` where status is failed.
- `charging_success_rate`: completed positive-energy sessions divided by completed-or-failed sessions, multiplied by 100.
- `completed_energy_delivered_kwh`: sum delivered kWh for completed positive-energy sessions.
- `average_successful_charging_duration_minutes`: average duration for completed positive-energy sessions.
- `completed_service_visit_count`: `COUNT(*)` where visit status is completed.
- `repeat_issue_service_visit_count`: completed visits where `is_repeat_issue` is true.
- `charging_station_count`: `COUNT(*)` on `charging_station_analytics_v1`.
- `operational_charging_station_count`: station count where status is operational.

Never infer historical ownership from the current-customer fields. Battery SOH
is descriptive and must not be presented as a failure prediction.

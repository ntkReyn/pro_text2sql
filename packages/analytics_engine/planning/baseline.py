"""Deterministic Vietnamese baseline for the Week 1 evaluation fixture.

This is deliberately a small, inspectable baseline rather than the target LLM
planner.  It establishes a reproducible lower bound and exercises the same
``SemanticQueryPlan`` contract that the Wren/Datus adapters will consume.
"""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Sequence

from pydantic import BaseModel, ConfigDict

from packages.domain import GroundedValue, PlanningTrace, SemanticQueryPlan
from packages.semantic_layer import SemanticCatalog
from packages.shared.text import normalize_vietnamese


class PlanningStatus(StrEnum):
    PLANNED = "planned"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNANSWERABLE = "unanswerable"


class BaselinePlanningResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: PlanningStatus
    normalized_question: str
    plan: SemanticQueryPlan | None = None
    message: str | None = None
    trace: PlanningTrace | None = None


class BaselinePlanner:
    """Rule baseline for known MVP intents, values, and explicit periods."""

    _CHARGING_METRICS = {
        "successful_charging_session_count",
        "failed_charging_session_count",
        "charging_success_rate",
        "completed_energy_delivered_kwh",
        "average_successful_charging_duration_minutes",
    }
    _TIME_METRICS = _CHARGING_METRICS | {
        "completed_service_visit_count",
        "repeat_issue_service_visit_count",
    }

    def __init__(self, catalog: SemanticCatalog) -> None:
        self._catalog = catalog

    def plan(
        self,
        question: str,
        *,
        grounded_values: Sequence[GroundedValue] = (),
    ) -> BaselinePlanningResult:
        normalized = normalize_vietnamese(question)
        metric_id = self._resolve_metric(normalized)
        if metric_id is None:
            return BaselinePlanningResult(
                status=PlanningStatus.UNANSWERABLE,
                normalized_question=normalized,
                message="Baseline chưa ánh xạ được câu hỏi tới metric được quản trị.",
            )

        time_range = self._resolve_time_range(normalized)
        if metric_id in self._TIME_METRICS and time_range is None:
            return BaselinePlanningResult(
                status=PlanningStatus.NEEDS_CLARIFICATION,
                normalized_question=normalized,
                message="Metric này cần tháng, quý hoặc năm cụ thể.",
            )

        dimensions = self._resolve_dimensions(normalized, metric_id)
        filters = self._resolve_filters(normalized, metric_id, grounded_values)
        sort = self._resolve_sort(normalized, metric_id, dimensions)
        limit = self._resolve_limit(normalized)

        plan = SemanticQueryPlan.model_validate(
            {
                "metric_id": metric_id,
                "metric_version": "1.0.0",
                "dimensions": dimensions,
                "filters": filters,
                "time_range": time_range,
                "grain": dimensions,
                "sort": sort,
                "limit": limit,
                "assumptions": [],
            }
        )
        # Fail fast if a rule accidentally emits a metric not present in the catalog.
        self._catalog.metric(plan.metric_id, plan.metric_version)
        return BaselinePlanningResult(
            status=PlanningStatus.PLANNED,
            normalized_question=normalized,
            plan=plan,
        )

    @staticmethod
    def _resolve_metric(question: str) -> str | None:
        if any(term in question for term in ("du bao", "nguy co", "se hong", "tuan toi")):
            return None
        if "kwh" in question or "dien nang" in question:
            return "completed_energy_delivered_kwh"
        if "sac" in question:
            if "ty le" in question and "thanh cong" in question:
                return "charging_success_rate"
            if "thoi luong" in question and "trung binh" in question:
                return "average_successful_charging_duration_minutes"
            if "that bai" in question:
                return "failed_charging_session_count"
            if "thanh cong" in question:
                return "successful_charging_session_count"
            if "tram" in question:
                if "dang hoat dong" in question:
                    return "operational_charging_station_count"
                return "charging_station_count"
        if "dich vu" in question or "bao duong" in question or "sua chua" in question:
            if "lap lai" in question or "tai dien" in question:
                return "repeat_issue_service_visit_count"
            if "hoan tat" in question or "hoan thanh" in question:
                return "completed_service_visit_count"
        if "soh" in question or "suc khoe pin" in question:
            if "duoi 80" in question or "can theo doi" in question:
                return "battery_watch_vehicle_count"
            if "trung binh" in question:
                return "average_latest_battery_soh_pct"
        if "khach hang" in question:
            return "customer_count"
        if re.search(r"\bxe\b", question):
            return "vehicle_count"
        return None

    @staticmethod
    def _resolve_dimensions(question: str, metric_id: str) -> list[str]:
        if "theo khu vuc tram" in question or "theo vung tram" in question:
            return ["station_region_code"]
        if "khu vuc khach hang" in question or "vung khach hang" in question:
            return ["customer_region_code"]
        if "theo tinh" in question or "tinh nao" in question or "thanh pho nao" in question:
            return ["province_name"]
        if "theo loai tram" in question:
            return ["station_scope"]
        if "theo tram" in question or "tram nao" in question:
            return ["station_name"]
        if "theo dong xe" in question or "dong xe nao" in question:
            return ["vehicle_model_code"]
        if "theo phan khuc" in question or "phan khuc nao" in question:
            return ["customer_segment"]
        if "theo trung tam" in question or "trung tam nao" in question:
            return ["service_center_code"]
        if "theo nhom loi" in question or "nhom loi nao" in question:
            return ["service_issue_category"]
        if "theo tuan" in question and metric_id in BaselinePlanner._CHARGING_METRICS:
            return ["charging_week"]
        if "theo thang" in question and metric_id in BaselinePlanner._CHARGING_METRICS:
            return ["charging_month"]
        return []

    def _resolve_filters(
        self,
        question: str,
        metric_id: str,
        grounded_values: Sequence[GroundedValue],
    ) -> list[dict[str, object]]:
        filters: list[dict[str, object]] = []
        allowed_fields = set(
            self._catalog.metric(metric_id, "1.0.0").allowed_filter_fields
        )
        for grounded in grounded_values:
            if grounded.field in allowed_fields:
                filters.append(
                    {
                        "field": grounded.field,
                        "operator": "eq",
                        "value": grounded.canonical_value,
                    }
                )

        grounded_fields = {item["field"] for item in filters}
        if "cong cong" in question and metric_id in BaselinePlanner._CHARGING_METRICS:
            if "station_scope" not in grounded_fields:
                filters.append(
                    {"field": "station_scope", "operator": "eq", "value": "public"}
                )
        province_values = {
            "ha noi": "Ha Noi",
            "da nang": "Da Nang",
            "ho chi minh": "Ho Chi Minh",
        }
        for alias, value in province_values.items():
            if alias in question and metric_id in BaselinePlanner._CHARGING_METRICS:
                if "province_name" not in grounded_fields:
                    filters.append(
                        {"field": "province_name", "operator": "eq", "value": value}
                    )
                break
        if metric_id == "vehicle_count" and "dang hoat dong" in question:
            if "vehicle_status" not in grounded_fields:
                filters.append(
                    {"field": "vehicle_status", "operator": "eq", "value": "active"}
                )
        return filters

    @staticmethod
    def _resolve_time_range(question: str) -> dict[str, date] | None:
        quarter_match = re.search(r"\bquy\s*([1-4])\s+nam\s+(\d{4})\b", question)
        if quarter_match:
            quarter = int(quarter_match.group(1))
            year = int(quarter_match.group(2))
            start_month = 1 + (quarter - 1) * 3
            end_year = year + (1 if start_month == 10 else 0)
            end_month = 1 if start_month == 10 else start_month + 3
            return {
                "start": date(year, start_month, 1),
                "end_exclusive": date(end_year, end_month, 1),
            }

        month_match = re.search(r"\bthang\s*(1[0-2]|[1-9])\s+nam\s+(\d{4})\b", question)
        if month_match:
            month = int(month_match.group(1))
            year = int(month_match.group(2))
            end_year = year + (1 if month == 12 else 0)
            end_month = 1 if month == 12 else month + 1
            return {
                "start": date(year, month, 1),
                "end_exclusive": date(end_year, end_month, 1),
            }

        year_match = re.search(r"\bnam\s+(\d{4})\b", question)
        if year_match:
            year = int(year_match.group(1))
            return {"start": date(year, 1, 1), "end_exclusive": date(year + 1, 1, 1)}
        return None

    @staticmethod
    def _resolve_sort(
        question: str,
        metric_id: str,
        dimensions: list[str],
    ) -> list[dict[str, str]]:
        if not dimensions:
            return []
        if dimensions[0] in {"charging_week", "charging_month", "service_month"}:
            return [{"field": dimensions[0], "direction": "asc"}]
        direction = "asc" if "thap nhat" in question or "it nhat" in question else "desc"
        return [{"field": metric_id, "direction": direction}]

    @staticmethod
    def _resolve_limit(question: str) -> int:
        top_match = re.search(r"\btop\s*(\d+)\b", question)
        if top_match:
            return min(int(top_match.group(1)), 500)
        return 1 if re.search(r"\bnao\b.*\bnhat\b", question) else 100

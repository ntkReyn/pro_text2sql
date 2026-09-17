"""Contracts for SQL policy and read-only execution."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ValidationDecision(StrEnum):
    PASS = "pass"
    REJECT = "reject"


class SQLSecurityReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: ValidationDecision
    statement_type: str | None = None
    referenced_relations: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    error_code: str | None = None


class QueryExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int = Field(ge=0)
    truncated: bool
    duration_ms: int = Field(ge=0)


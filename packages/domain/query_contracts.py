"""Versioned contracts shared by planning, validation, and SQL generation."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


Identifier = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=80),
]
ScalarValue = str | int | float | bool | date


class FilterOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class TimeRange(BaseModel):
    """Half-open business time range: ``start <= t < end_exclusive``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    start: date
    end_exclusive: date

    @model_validator(mode="after")
    def validate_range(self) -> "TimeRange":
        if self.start >= self.end_exclusive:
            raise ValueError("time range start must be before end_exclusive")
        return self


class QueryFilter(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: Identifier
    operator: FilterOperator
    value: ScalarValue | list[ScalarValue]

    @model_validator(mode="after")
    def validate_operator_value(self) -> "QueryFilter":
        if self.operator is FilterOperator.IN:
            if not isinstance(self.value, list) or not self.value:
                raise ValueError("the 'in' operator requires a non-empty list")
        elif isinstance(self.value, list):
            raise ValueError(f"the '{self.operator}' operator requires a scalar value")
        return self


class SortSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: Identifier
    direction: SortDirection = SortDirection.DESC


class SemanticQueryPlan(BaseModel):
    """LLM-proposed intent representation; never executable without validation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_version: Literal["1.0"] = "1.0"
    metric_id: Identifier
    metric_version: Annotated[str, StringConstraints(min_length=1, max_length=32)]
    dimensions: list[Identifier] = Field(default_factory=list, max_length=5)
    filters: list[QueryFilter] = Field(default_factory=list, max_length=20)
    time_range: TimeRange | None = None
    grain: list[Identifier] = Field(default_factory=list, max_length=5)
    sort: list[SortSpec] = Field(default_factory=list, max_length=3)
    limit: int = Field(default=100, ge=1, le=500)
    assumptions: list[str] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def validate_shape(self) -> "SemanticQueryPlan":
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("dimensions must be unique")
        if len(set(self.grain)) != len(self.grain):
            raise ValueError("grain fields must be unique")
        if set(self.grain) != set(self.dimensions):
            raise ValueError("output grain must contain exactly the selected dimensions")
        if len({item.field for item in self.sort}) != len(self.sort):
            raise ValueError("sort fields must be unique")
        return self


class SQLCandidate(BaseModel):
    """Parameterized SQL produced by a deterministic compiler."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sql: str
    parameters: dict[str, ScalarValue]
    dialect: Literal["postgres"] = "postgres"
    metric_id: Identifier
    metric_version: str
    plan_version: Literal["1.0"] = "1.0"

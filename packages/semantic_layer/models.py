"""Validated models for trusted semantic catalog files."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from packages.domain.query_contracts import FilterOperator, Identifier


class CatalogStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


class DimensionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: Identifier
    label: str
    description: str
    expression: str
    data_type: str
    aliases_vi: list[str] = Field(default_factory=list)
    allowed_operators: list[FilterOperator] = Field(default_factory=list)

    @field_validator("expression")
    @classmethod
    def expression_must_not_contain_statement_separator(cls, value: str) -> str:
        if ";" in value or "--" in value or "/*" in value:
            raise ValueError("catalog expressions cannot contain SQL statement separators/comments")
        return value


class MetricDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: Identifier
    version: Annotated[str, StringConstraints(min_length=1, max_length=32)]
    status: CatalogStatus
    label: str
    description: str
    business_owner: str
    technical_owner: str
    base_relation: str
    base_grain: list[Identifier]
    expression: str
    base_filters: list[str] = Field(default_factory=list)
    time_dimension: str | None
    allowed_dimensions: list[Identifier]
    allowed_filter_fields: list[Identifier]
    unit: str
    freshness_requirement: str
    classification: str
    effective_from: str

    @field_validator("base_relation")
    @classmethod
    def relation_must_be_qualified_identifier(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)?", value):
            raise ValueError("base_relation must be a trusted qualified identifier")
        return value

    @field_validator("expression", "time_dimension")
    @classmethod
    def sql_fragment_must_be_single_expression(cls, value: str | None) -> str | None:
        if value is not None and (";" in value or "--" in value or "/*" in value):
            raise ValueError("catalog SQL fragments cannot contain separators/comments")
        return value

    @field_validator("base_filters")
    @classmethod
    def filters_must_be_single_expressions(cls, values: list[str]) -> list[str]:
        if any(";" in value or "--" in value or "/*" in value for value in values):
            raise ValueError("catalog filters cannot contain separators/comments")
        return values

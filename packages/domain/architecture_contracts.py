"""Typed contracts for the pre-Wren planning and retrieval stages."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.query_contracts import Identifier, ScalarValue


class GateDecision(StrEnum):
    CLEAR = "clear"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class NormalizedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    original: str
    normalized: str
    canonical: str
    matched_aliases: list[str] = Field(default_factory=list)


class GroundedValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    field: Identifier
    canonical_value: ScalarValue
    matched_alias: str
    source_version: str
    confidence: float = Field(ge=0.0, le=1.0)


class PreliminaryIntentSketch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_candidates: list[Identifier] = Field(default_factory=list, max_length=5)
    dimension_candidates: list[Identifier] = Field(default_factory=list, max_length=5)
    filter_fields: list[Identifier] = Field(default_factory=list, max_length=10)
    operations: list[str] = Field(default_factory=list, max_length=10)
    has_time_scope: bool = False
    requested_limit: int | None = Field(default=None, ge=1, le=500)
    structure_tokens: list[str] = Field(default_factory=list, max_length=30)


class RetrievedExample(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    case_id: str
    question: str
    metric_id: Identifier
    semantic_similarity: float = Field(ge=0.0, le=1.0)
    structure_similarity: float = Field(ge=0.0, le=1.0)
    governed_overlap: float = Field(ge=0.0, le=1.0)
    verified_quality: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=1.0)


class PlanningTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    architecture_version: str = "b1.0"
    canonical_question: str
    gate_decision: GateDecision
    gate_message: str | None = None
    grounded_values: list[GroundedValue] = Field(default_factory=list)
    preliminary_intent: PreliminaryIntentSketch | None = None
    retrieved_examples: list[RetrievedExample] = Field(default_factory=list)
    plan_validation: str = "not_run"

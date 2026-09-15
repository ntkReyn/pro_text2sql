"""B1 pipeline matching the target Datus/Wren architecture through local ports."""

from __future__ import annotations

from packages.analytics_engine.language import VietnameseNormalizer
from packages.analytics_engine.planning.baseline import (
    BaselinePlanner,
    BaselinePlanningResult,
    PlanningStatus,
)
from packages.analytics_engine.planning.gates import AnswerabilityGate
from packages.analytics_engine.retrieval import (
    PreliminaryIntentSketcher,
    SemanticDAILSelector,
)
from packages.analytics_engine.validation import SemanticPlanValidator
from packages.domain import GateDecision, PlanningTrace
from packages.semantic_layer import (
    GovernedValueIndex,
    SemanticCatalog,
    load_default_value_index,
)


class ArchitectureBaselinePipeline:
    """Execute the new pre-LLM stages while preserving the deterministic B0 planner."""

    def __init__(
        self,
        catalog: SemanticCatalog,
        *,
        value_index: GovernedValueIndex | None = None,
    ) -> None:
        self._catalog = catalog
        self._normalizer = VietnameseNormalizer()
        self._gate = AnswerabilityGate()
        self._value_index = value_index or load_default_value_index(catalog)
        self._sketcher = PreliminaryIntentSketcher(catalog)
        self._selector = SemanticDAILSelector.default(catalog, self._sketcher)
        self._baseline = BaselinePlanner(catalog)
        self._validator = SemanticPlanValidator(catalog)

    def plan(self, question: str) -> BaselinePlanningResult:
        normalized = self._normalizer.normalize(question)
        grounded_values = self._value_index.ground(normalized.normalized)
        gate = self._gate.evaluate(normalized)
        if gate.decision is not GateDecision.CLEAR:
            status = (
                PlanningStatus.NEEDS_CLARIFICATION
                if gate.decision is GateDecision.CLARIFY
                else PlanningStatus.UNANSWERABLE
            )
            return BaselinePlanningResult(
                status=status,
                normalized_question=normalized.normalized,
                message=gate.message,
                trace=PlanningTrace(
                    canonical_question=normalized.canonical,
                    gate_decision=gate.decision,
                    gate_message=gate.message,
                    grounded_values=grounded_values,
                ),
            )

        sketch = self._sketcher.sketch(normalized.canonical, grounded_values)
        examples = self._selector.select(normalized.canonical, sketch)
        baseline_result = self._baseline.plan(
            normalized.canonical,
            grounded_values=grounded_values,
        )

        gate_decision = GateDecision.CLEAR
        if baseline_result.status is PlanningStatus.NEEDS_CLARIFICATION:
            gate_decision = GateDecision.CLARIFY
        elif baseline_result.status is PlanningStatus.UNANSWERABLE:
            gate_decision = GateDecision.ABSTAIN

        validation_status = "not_run"
        if baseline_result.plan is not None:
            self._validator.validate(
                baseline_result.plan,
                allow_draft_metrics=True,
            )
            validation_status = "passed"

        return BaselinePlanningResult(
            status=baseline_result.status,
            normalized_question=normalized.normalized,
            plan=baseline_result.plan,
            message=baseline_result.message,
            trace=PlanningTrace(
                canonical_question=normalized.canonical,
                gate_decision=gate_decision,
                gate_message=baseline_result.message,
                grounded_values=grounded_values,
                preliminary_intent=sketch,
                retrieved_examples=examples,
                plan_validation=validation_status,
            ),
        )

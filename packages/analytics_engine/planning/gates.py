"""Answerability and ambiguity checks that run before retrieval/generation."""

from __future__ import annotations

from dataclasses import dataclass

from packages.domain import GateDecision, NormalizedQuestion


@dataclass(frozen=True)
class GateResult:
    decision: GateDecision
    message: str | None = None


class AnswerabilityGate:
    """Small deterministic policy baseline; an LLM may propose, never override it."""

    def evaluate(self, question: NormalizedQuestion) -> GateResult:
        value = question.canonical
        if any(term in value for term in ("du bao", "nguy co", "se hong", "tuan toi")):
            return GateResult(
                GateDecision.ABSTAIN,
                "MVP analytics mô tả không trả lời câu hỏi dự báo hoặc chẩn đoán.",
            )
        if "hieu qua sac" in value or "chat luong sac" in value:
            return GateResult(
                GateDecision.CLARIFY,
                "Bạn muốn đánh giá tỷ lệ thành công, điện năng hay thời lượng sạc?",
            )
        if "sac thanh cong" in value and not any(
            term in value
            for term in ("ty le", "bao nhieu", "so phien", "dem", "trung binh")
        ):
            return GateResult(
                GateDecision.CLARIFY,
                "Bạn muốn tỷ lệ hay số phiên sạc thành công?",
            )
        if ("suc khoe pin" in value or "soh" in value) and not any(
            term in value for term in ("trung binh", "duoi 80", "bao nhieu", "can theo doi")
        ):
            return GateResult(
                GateDecision.CLARIFY,
                "Bạn muốn SOH trung bình hay số xe dưới ngưỡng theo dõi 80%?",
            )
        return GateResult(GateDecision.CLEAR)

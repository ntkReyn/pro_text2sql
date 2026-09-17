"""LLM adapter used by the Wren-first text-to-SQL workflow."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Literal

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field

from packages.integrations.settings import WrenSettings


class LLMGenerationError(RuntimeError):
    """A safe, user-facing error from the configured LLM provider."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class WrenAgentProposal(BaseModel):
    """The only output accepted from the LLM before Wren validates it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["ready", "clarify", "unanswerable"]
    sql: str | None = None
    message: str | None = None
    assumptions: list[str] = Field(default_factory=list, max_length=10)


_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "wren_sql_proposal",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["ready", "clarify", "unanswerable"],
                },
                "sql": {"type": ["string", "null"]},
                "message": {"type": ["string", "null"]},
                "assumptions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 10,
                },
            },
            "required": ["status", "sql", "message", "assumptions"],
        },
    },
}


class OpenAIWrenAgent:
    """Ask an OpenAI-compatible model to write SQL against Wren models.

    This class deliberately does not execute SQL and does not know physical
    database tables. Wren is the next, authoritative validation boundary.
    """

    def __init__(
        self,
        settings: WrenSettings,
        *,
        client: OpenAI | None = None,
    ) -> None:
        self._settings = settings
        self._client = client

    async def propose(
        self,
        *,
        question: str,
        context: str,
        feedback: str | None = None,
    ) -> WrenAgentProposal:
        return await asyncio.to_thread(
            self._propose_sync,
            question=question,
            context=context,
            feedback=feedback,
        )

    def _propose_sync(
        self,
        *,
        question: str,
        context: str,
        feedback: str | None,
    ) -> WrenAgentProposal:
        if not self._settings.llm_configured:
            raise LLMGenerationError("llm_not_configured")

        client = self._client or OpenAI(
            api_key=self._settings.llm_api_key,
            base_url=self._settings.llm_base_url or None,
            timeout=self._settings.llm_timeout_ms / 1000,
            max_retries=self._settings.llm_max_retries,
        )

        user_prompt = f"""User question:
{question}

Wren project context:
{context}
"""
        if feedback:
            user_prompt += f"""

The previous SQL proposal was rejected. Repair only the issue described below
and return a complete replacement proposal:
{feedback}
"""

        request: dict[str, Any] = {
            "model": self._settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": _system_prompt(),
                },
                {"role": "user", "content": user_prompt},
            ],
            "max_completion_tokens": self._settings.llm_max_output_tokens,
            "response_format": _RESPONSE_FORMAT,
        }
        # Reasoning models reject temperature in some OpenAI-compatible APIs.
        if self._settings.llm_reasoning_effort:
            request["reasoning_effort"] = self._settings.llm_reasoning_effort
        elif self._settings.llm_temperature is not None:
            request["temperature"] = self._settings.llm_temperature

        try:
            response = client.chat.completions.create(**request)
        except Exception as exc:
            raise LLMGenerationError("llm_request_failed") from exc

        try:
            content = response.choices[0].message.content or ""
            payload = _parse_json_object(content)
            return WrenAgentProposal.model_validate(payload)
        except Exception as exc:
            raise LLMGenerationError("llm_invalid_output") from exc


def _system_prompt() -> str:
    return """You are the SQL agent in a Wren Engine workflow.

Wren models are the semantic interface. Write PostgreSQL-compatible SQL against
the logical model names and exposed columns in the supplied Wren context. Never
use physical database table names, invent columns, or redefine a business rule.
Use the knowledge rules and confirmed examples when they apply.

Return exactly one JSON object with:
- status: ready when a query can be written, clarify when the question needs
  one missing business/time choice, or unanswerable when the Wren context cannot
  answer it;
- sql: one read-only SELECT with a LIMIT between 1 and 1000 when status=ready,
  otherwise null;
- message: a concise Vietnamese explanation for clarify/unanswerable;
- assumptions: explicit assumptions, if any.

Do not return Markdown fences or commentary. A query must be a single SELECT,
must use only Wren model names, and must include LIMIT. Prefer explicit columns
over SELECT * for analytical questions.
"""


def _parse_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE
        )
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise TypeError("LLM output is not a JSON object")
    return payload

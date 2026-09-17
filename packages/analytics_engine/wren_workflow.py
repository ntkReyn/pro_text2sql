"""Wren-first text-to-SQL workflow.

The LLM behaves like the agent in Wren's CLI workflow: it reads MDL and
knowledge, writes SQL against logical Wren models, and asks Wren to dry-plan it.
The workflow has no second planner or provider bridge.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from packages.analytics_engine.validation import WrenSQLSecurityValidator
from packages.analytics_engine.wren_memory import WrenMemoryService
from packages.analytics_engine.wren_runtime import WrenNativeRuntime
from packages.data_platform import PostgreSQLReadOnlyExecutor
from packages.domain import (
    QueryExecutionResult,
    SQLSecurityReport,
    ValidationDecision,
)
from packages.integrations import (
    LLMGenerationError,
    OpenAIWrenAgent,
    WrenAgentProposal,
    WrenSettings,
)


class WrenWorkflowStatus(str):
    PLANNED = "planned"
    EXECUTED = "executed"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNANSWERABLE = "unanswerable"
    FAILED = "failed"


class WrenModelSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    description: str | None = None
    columns: list[str] = Field(default_factory=list)


class WrenContextSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project: str
    models: list[WrenModelSummary]
    knowledge_files: list[str] = Field(default_factory=list)
    confirmed_query_count: int = 0
    memory_backend: str = "grep"
    memory_strategy: str = "full"


class WrenWorkflowTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_version: str = "wren-first.v1"
    context_loaded: bool = False
    dry_plan_attempts: int = 0
    repair_attempts: int = 0
    stages: list[str] = Field(default_factory=list)


class WrenQueryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    question: str
    message: str | None = None
    sql: str | None = None
    planned_sql: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    context: WrenContextSummary
    security: SQLSecurityReport | None = None
    execution: QueryExecutionResult | None = None
    trace: WrenWorkflowTrace


class WrenAgent(Protocol):
    async def propose(
        self,
        *,
        question: str,
        context: str,
        feedback: str | None = None,
    ) -> WrenAgentProposal: ...


@dataclass(frozen=True)
class WrenContextSnapshot:
    project_path: Path
    manifest: dict[str, Any]
    prompt: str
    summary: WrenContextSummary


class WrenProjectContext:
    def __init__(
        self,
        project_path: str | Path,
        *,
        memory_backend: str = "auto",
        memory_path: str | Path | None = None,
        memory_schema_threshold: int = 30_000,
    ) -> None:
        self._project_path = Path(project_path).resolve()
        self._memory = WrenMemoryService(
            self._project_path,
            backend=memory_backend,
            memory_path=memory_path,
            schema_threshold=memory_schema_threshold,
        )

    def load(self, question: str | None = None) -> WrenContextSnapshot:
        try:
            from wren.context import build_json, load_rules
        except ImportError as exc:
            raise RuntimeError("wren_sdk_unavailable") from exc

        manifest = build_json(self._project_path)
        schema_context = self._memory.fetch(
            manifest,
            question or "",
            limit=5,
        )
        schema_text = _schema_text(schema_context)
        rules, _ = load_rules(self._project_path)
        knowledge_files = self._knowledge_files()
        recalled = self._memory.recall(question, limit=3) if question else []
        examples = (
            _recall_examples(recalled)
            if question
            else self._load_examples()
        )
        memory_status = self._memory.status(manifest)
        models = _summarize_models(manifest)
        summary = WrenContextSummary(
            project=self._project_path.name,
            models=models,
            knowledge_files=knowledge_files,
            confirmed_query_count=len(recalled) if question else len(examples),
            memory_backend=memory_status.backend,
            memory_strategy=str(schema_context.get("strategy", "full")),
        )
        prompt = _context_prompt(
            project_name=self._project_path.name,
            schema_text=schema_text,
            rules=rules,
            examples=examples,
        )
        return WrenContextSnapshot(
            project_path=self._project_path,
            manifest=manifest,
            prompt=prompt,
            summary=summary,
        )

    def _knowledge_files(self) -> list[str]:
        knowledge = self._project_path / "knowledge"
        if not knowledge.is_dir():
            return []
        return [
            path.relative_to(self._project_path).as_posix()
            for path in sorted(knowledge.rglob("*"))
            if path.is_file() and path.suffix.lower() in {".md", ".yml", ".yaml"}
        ]

    def _load_examples(self) -> list[str]:
        sql_dir = self._project_path / "knowledge" / "sql"
        if not sql_dir.is_dir():
            return []
        examples: list[str] = []
        for path in sorted(sql_dir.glob("*.md"))[:10]:
            examples.append(path.read_text(encoding="utf-8")[:8_000])
        return examples


class WrenFirstWorkflow:
    def __init__(
        self,
        settings: WrenSettings,
        *,
        agent: WrenAgent | None = None,
        executor: PostgreSQLReadOnlyExecutor | None = None,
    ) -> None:
        self._settings = settings
        self._context = WrenProjectContext(
            settings.wren_project_path,
            memory_backend=settings.wren_memory_backend,
            memory_path=settings.wren_memory_path or None,
            memory_schema_threshold=settings.wren_memory_schema_threshold,
        )
        self._agent = agent or OpenAIWrenAgent(settings)
        self._validator = WrenSQLSecurityValidator(max_rows=settings.wren_max_sql_rows)
        # Embedders may inject a bounded executor for compatibility. The API
        # path leaves this unset so normal execution uses WrenEngine directly.
        self._executor = executor
        self._runtime = WrenNativeRuntime()

    async def run(self, question: str, *, execute: bool = False) -> WrenQueryResponse:
        trace = WrenWorkflowTrace(stages=["load_context"])
        try:
            context = await asyncio.to_thread(self._context.load, question.strip())
        except Exception:  # noqa: BLE001 - context loading must fail closed
            trace = trace.model_copy(update={"context_loaded": False})
            return self._failed(question, "wren_context_unavailable", trace)

        trace = trace.model_copy(
            update={"context_loaded": True, "stages": ["load_context", "propose_sql"]}
        )
        feedback: str | None = None
        last_sql: str | None = None
        last_report: SQLSecurityReport | None = None

        for attempt in range(self._settings.wren_max_repair_attempts + 1):
            try:
                proposal = await self._agent.propose(
                    question=question,
                    context=context.prompt,
                    feedback=feedback,
                )
            except LLMGenerationError as exc:
                return self._failed(question, exc.code, trace)

            if proposal.status != "ready":
                status = (
                    WrenWorkflowStatus.NEEDS_CLARIFICATION
                    if proposal.status == "clarify"
                    else WrenWorkflowStatus.UNANSWERABLE
                )
                return WrenQueryResponse(
                    status=status,
                    question=question,
                    message=proposal.message,
                    assumptions=proposal.assumptions,
                    context=context.summary,
                    trace=trace.model_copy(
                        update={"repair_attempts": attempt, "stages": trace.stages}
                    ),
                )

            if not proposal.sql:
                feedback = "status=ready requires a non-empty SQL string"
                continue

            last_sql = proposal.sql
            last_report = self._validator.inspect(
                proposal.sql,
                context.manifest,
                stage="logical",
            )
            trace = trace.model_copy(
                update={
                    "repair_attempts": attempt,
                    "stages": ["load_context", "propose_sql", "validate_sql"],
                }
            )
            if last_report.decision is ValidationDecision.REJECT:
                feedback = f"logical SQL policy rejected the proposal: {last_report.error_code}"
                continue

            try:
                planned_sql = await asyncio.to_thread(
                    self._dry_plan,
                    context,
                    proposal.sql,
                )
            except Exception as exc:  # noqa: BLE001 - Wren exposes backend-specific errors
                feedback = f"Wren dry_plan rejected the SQL: {_safe_error(exc)}"
                continue

            trace = trace.model_copy(
                update={
                    "dry_plan_attempts": attempt + 1,
                    "repair_attempts": attempt,
                    "stages": ["load_context", "propose_sql", "validate_sql", "dry_plan"],
                }
            )
            expanded_report = self._validator.inspect(
                planned_sql,
                context.manifest,
                stage="expanded",
            )
            if expanded_report.decision is ValidationDecision.REJECT:
                feedback = f"expanded Wren SQL policy rejected the plan: {expanded_report.error_code}"
                last_report = expanded_report
                continue

            execution = None
            status = WrenWorkflowStatus.PLANNED
            stages = ["load_context", "propose_sql", "validate_sql", "dry_plan"]
            if execute:
                try:
                    if self._executor is not None:
                        execution = await asyncio.to_thread(
                            self._executor.execute_sql,
                            planned_sql,
                            {},
                        )
                    else:
                        execution = await asyncio.to_thread(
                            self._runtime.query,
                            context.manifest,
                            proposal.sql,
                            database_url=self._settings.analytics_database_url,
                            max_rows=self._settings.wren_max_sql_rows,
                            statement_timeout_ms=self._settings.analytics_database_statement_timeout_ms,
                        )
                except Exception as exc:  # noqa: BLE001 - execution must fail closed
                    return self._failed(
                        question,
                        _safe_error(exc),
                        trace.model_copy(update={"stages": stages + ["execute"]}),
                        sql=proposal.sql,
                        planned_sql=planned_sql,
                        context=context.summary,
                        security=expanded_report,
                    )
                status = WrenWorkflowStatus.EXECUTED
                stages.append("execute")

            return WrenQueryResponse(
                status=status,
                question=question,
                sql=proposal.sql,
                planned_sql=planned_sql,
                assumptions=proposal.assumptions,
                context=context.summary,
                security=expanded_report,
                execution=execution,
                trace=trace.model_copy(update={"stages": stages}),
            )

        return self._failed(
            question,
            "wren_repair_exhausted",
            trace,
            sql=last_sql,
            context=context.summary,
            security=last_report,
        )

    def _dry_plan(self, context: WrenContextSnapshot, sql: str) -> str:
        return self._runtime.dry_plan(context.manifest, sql)

    @staticmethod
    def _failed(
        question: str,
        code: str,
        trace: WrenWorkflowTrace,
        *,
        sql: str | None = None,
        planned_sql: str | None = None,
        context: WrenContextSummary | None = None,
        security: SQLSecurityReport | None = None,
    ) -> WrenQueryResponse:
        return WrenQueryResponse(
            status=WrenWorkflowStatus.FAILED,
            question=question,
            message=code,
            sql=sql,
            planned_sql=planned_sql,
            context=context
            or WrenContextSummary(project="unknown", models=[]),
            security=security,
            trace=trace,
        )


def _summarize_models(manifest: dict[str, Any]) -> list[WrenModelSummary]:
    result: list[WrenModelSummary] = []
    for model in manifest.get("models", []) or []:
        if not isinstance(model, dict) or not model.get("name"):
            continue
        properties = model.get("properties") or {}
        description = model.get("description") or properties.get("description")
        columns = [
            str(column.get("name"))
            for column in model.get("columns", []) or []
            if isinstance(column, dict) and column.get("name")
        ]
        result.append(
            WrenModelSummary(
                name=str(model["name"]),
                description=description,
                columns=columns,
            )
        )
    return result


def _context_prompt(
    *,
    project_name: str,
    schema_text: str,
    rules: str | None,
    examples: list[str],
) -> str:
    parts = [f"Project: {project_name}", "\nWREN SCHEMA:\n" + schema_text]
    if rules:
        parts.append("\nBUSINESS RULES:\n" + rules[:20_000])
    if examples:
        parts.append("\nCONFIRMED NL-SQL EXAMPLES:\n" + "\n\n".join(examples))
    return "\n".join(parts)[:50_000]


def _schema_text(schema_context: dict[str, Any]) -> str:
    if schema_context.get("strategy") == "full":
        return str(schema_context.get("schema", ""))
    results = schema_context.get("results", []) or []
    return "\n\n".join(
        str(item.get("text", ""))
        for item in results
        if isinstance(item, dict) and item.get("text")
    )


def _recall_examples(rows: list[dict[str, Any]]) -> list[str]:
    examples: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        nl = row.get("nl_query") or row.get("nl")
        sql = row.get("sql_query") or row.get("sql")
        if nl and sql:
            examples.append(f"Question: {nl}\nSQL: {sql}")
    return examples


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip().replace("\n", " ")
    return text[:500] or type(exc).__name__

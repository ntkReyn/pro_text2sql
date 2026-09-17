"""Configuration for the Wren-first text-to-SQL runtime."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int_env(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        return float(_env(name, str(default)))
    except ValueError:
        return default


class WrenSettings(BaseModel):
    """Single runtime configuration; Wren is the only query authority."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    wren_project_path: str = "wren/ev_analytics"
    wren_max_sql_rows: int = Field(default=1_000, ge=1, le=10_000)
    wren_max_repair_attempts: int = Field(default=2, ge=0, le=5)
    wren_memory_backend: str = "auto"
    wren_memory_path: str = ""
    wren_memory_schema_threshold: int = Field(default=30_000, ge=1_000, le=200_000)

    llm_provider: str = "openai"
    llm_model: str = "gpt-5.6-terra"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout_ms: int = Field(default=30_000, ge=100, le=120_000)
    llm_max_retries: int = Field(default=2, ge=0, le=5)
    llm_reasoning_effort: str = "medium"
    llm_temperature: float | None = Field(default=0.0, ge=0.0, le=2.0)
    llm_max_output_tokens: int = Field(default=1_500, ge=256, le=8_000)

    analytics_execution_enabled: bool = False
    analytics_database_url: str = ""
    analytics_database_statement_timeout_ms: int = Field(
        default=15_000,
        ge=100,
        le=60_000,
    )
    analytics_database_max_rows: int = Field(default=1_000, ge=1, le=10_000)

    @classmethod
    def from_env(cls) -> WrenSettings:
        temperature_raw = _env("LLM_TEMPERATURE", "0")
        temperature = (
            None
            if temperature_raw.lower() in {"", "none", "null"}
            else _float_env("LLM_TEMPERATURE", 0.0)
        )
        return cls(
            wren_project_path=_env("WREN_PROJECT_PATH", "wren/ev_analytics"),
            wren_max_sql_rows=_int_env("WREN_MAX_SQL_ROWS", 1_000),
            wren_max_repair_attempts=_int_env(
                "WORKFLOW_MAX_REPAIR_ATTEMPTS", 2
            ),
            wren_memory_backend=_env("WREN_MEMORY_BACKEND", "auto").lower(),
            wren_memory_path=_env("WREN_MEMORY_PATH"),
            wren_memory_schema_threshold=_int_env(
                "WREN_MEMORY_SCHEMA_THRESHOLD", 30_000
            ),
            llm_provider=_env("LLM_PROVIDER", "openai").lower(),
            llm_model=_env("LLM_MODEL", "gpt-5.6-terra"),
            llm_api_key=_env("LLM_API_KEY"),
            llm_base_url=_env("LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_timeout_ms=_int_env("LLM_TIMEOUT_MS", 30_000),
            llm_max_retries=_int_env("LLM_MAX_RETRIES", 2),
            llm_reasoning_effort=_env("LLM_REASONING_EFFORT", "medium"),
            llm_temperature=temperature,
            llm_max_output_tokens=_int_env("LLM_MAX_OUTPUT_TOKENS", 1_500),
            analytics_execution_enabled=_env(
                "ANALYTICS_EXECUTION_ENABLED", "false"
            ).lower()
            == "true",
            analytics_database_url=_env("ANALYTICS_DATABASE_URL"),
            analytics_database_statement_timeout_ms=_int_env(
                "ANALYTICS_DATABASE_STATEMENT_TIMEOUT_MS", 15_000
            ),
            analytics_database_max_rows=_int_env(
                "ANALYTICS_DATABASE_MAX_ROWS", 1_000
            ),
        )

    @property
    def wren_project(self) -> Path:
        return Path(self.wren_project_path).resolve()

    @property
    def wren_configured(self) -> bool:
        return (
            importlib.util.find_spec("wren") is not None
            and (self.wren_project / "wren_project.yml").is_file()
        )

    @property
    def llm_configured(self) -> bool:
        return self.llm_provider == "openai" and bool(self.llm_api_key)

    @property
    def database_configured(self) -> bool:
        placeholders = ("CHANGE_ME", "PROJECT_REF", "POOLER_HOST", "YOUR_")
        return bool(self.analytics_database_url) and not any(
            marker in self.analytics_database_url for marker in placeholders
        )

    def execution_settings(self):
        from packages.data_platform import ExecutionSettings

        return ExecutionSettings(
            enabled=self.analytics_execution_enabled,
            database_url=self.analytics_database_url,
            statement_timeout_ms=self.analytics_database_statement_timeout_ms,
            max_rows=self.analytics_database_max_rows,
        )

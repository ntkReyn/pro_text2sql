"""Wren-compatible schema and NL-to-SQL memory.

The markdown files under ``knowledge/sql`` are deliberately the source of
truth, exactly like Wren.  The optional LanceDB backend is only a derived
index; a dependency-free token/substring backend keeps the workflow useful
before a memory extra or a database is installed.
"""

from __future__ import annotations

import re
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_LOCK_GUARD = RLock()
_PROJECT_LOCKS: dict[tuple[str, str], RLock] = {}


def _project_lock(project_path: Path, memory_path: Path) -> RLock:
    key = (str(project_path), str(memory_path))
    with _LOCK_GUARD:
        return _PROJECT_LOCKS.setdefault(key, RLock())


class WrenMemoryStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backend: str
    memory_path: str
    query_pairs: int = Field(ge=0)
    schema_indexed: bool = False
    optional_semantic_backend: bool = False


class WrenMemoryService:
    """Project-scoped memory facade with Wren's fallback semantics."""

    def __init__(
        self,
        project_path: str | Path,
        *,
        backend: str = "auto",
        memory_path: str | Path | None = None,
        schema_threshold: int = 30_000,
    ) -> None:
        self.project_path = Path(project_path).resolve()
        self.memory_path = Path(memory_path).expanduser().resolve() if memory_path else (
            self.project_path / ".wren" / "memory"
        )
        self.backend_choice = backend
        self.schema_threshold = schema_threshold
        self._index: Any | None = None
        self._semantic_memory: Any | None = None
        self._semantic_memory_attempted = False
        # Wren warns that a LanceDB reindex replaces derived tables and can
        # transiently conflict with readers.  Share a lock across service
        # instances created by separate API requests for the same project.
        self._lock = _project_lock(self.project_path, self.memory_path)

    @staticmethod
    def describe_schema(manifest: dict[str, Any]) -> str:
        from wren.memory import WrenMemory

        return WrenMemory.describe_schema(manifest)

    def _get_index(self) -> Any:
        if self._index is None:
            from wren.memory.index_backend import get_index

            self._index = get_index(
                self.project_path,
                str(self.memory_path),
                backend=self.backend_choice,
            )
        return self._index

    def _get_semantic_memory(self) -> Any | None:
        if self._semantic_memory_attempted:
            return self._semantic_memory
        self._semantic_memory_attempted = True
        try:
            from wren.memory import WrenMemory

            self._semantic_memory = WrenMemory(path=self.memory_path)
        except (ImportError, ModuleNotFoundError, OSError, RuntimeError):
            # The Wren memory extra is intentionally optional.  The caller
            # falls back to the dependency-free implementation below.
            self._semantic_memory = None
        return self._semantic_memory

    def status(self, manifest: dict[str, Any] | None = None) -> WrenMemoryStatus:
        with self._lock:
            index = self._get_index()
            try:
                raw = index.status()
                backend = str(raw.get("backend", getattr(index, "name", "grep")))
                pairs = int(raw.get("pairs", raw.get("query_count", 0)) or 0)
            except Exception:  # noqa: BLE001 - optional derived index may be stale
                index = self._grep_index()
                raw = index.status()
                backend = "grep"
                pairs = int(raw.get("pairs", 0) or 0)
            schema_indexed = False
            semantic = self._get_semantic_memory()
            if semantic is not None and manifest is not None:
                try:
                    schema_indexed = bool(semantic.schema_is_current(manifest))
                except Exception:  # noqa: BLE001 - derived index is best effort
                    schema_indexed = False
            return WrenMemoryStatus(
                backend=backend,
                memory_path=str(self.memory_path),
                query_pairs=pairs,
                schema_indexed=schema_indexed,
                optional_semantic_backend=semantic is not None,
            )

    def index(self, manifest: dict[str, Any]) -> dict[str, Any]:
        """Build schema and query indexes without changing source markdown."""

        with self._lock:
            result: dict[str, Any] = {"source": "knowledge/sql/*.md"}
            semantic = self._get_semantic_memory()
            if semantic is not None:
                try:
                    result.update(
                        semantic.index_manifest(
                            manifest,
                            replace=True,
                            seed_queries=True,
                        )
                    )
                    result["schema_backend"] = "lancedb"
                except Exception as exc:  # noqa: BLE001 - degrade to grep safely
                    result["schema_backend"] = "grep"
                    result["schema_index_error"] = _safe_error(exc)
            else:
                result["schema_backend"] = "grep"
                result["schema_items"] = 0
                result["seed_queries"] = 0
            try:
                result.update(self._get_index().rebuild())
            except Exception as exc:  # noqa: BLE001 - derived index is optional
                self._index = self._grep_index()
                result["backend_fallback"] = _safe_error(exc)
                result.update(self._index.rebuild())
            return result

    def reset(self) -> None:
        """Drop only the derived index; source markdown remains untouched."""

        with self._lock:
            try:
                self._get_index().reset()
            except Exception:  # noqa: BLE001 - a missing derived index is already empty
                self._index = None
            self._index = None
            self._semantic_memory = None
            self._semantic_memory_attempted = False

    def fetch(
        self,
        manifest: dict[str, Any],
        query: str,
        *,
        limit: int = 5,
        item_type: str | None = None,
        model_name: str | None = None,
        threshold: int | None = None,
    ) -> dict[str, Any]:
        """Return schema context using Wren's full-or-search strategy."""

        schema = self.describe_schema(manifest)
        effective_threshold = threshold or self.schema_threshold
        if len(schema) <= effective_threshold:
            return {
                "strategy": "full",
                "schema": schema,
                "backend": self._backend_name(),
            }

        semantic = self._get_semantic_memory()
        if semantic is not None:
            try:
                if semantic.schema_is_current(manifest):
                    result = semantic.get_context(
                        manifest,
                        query,
                        limit=limit,
                        item_type=item_type,
                        model_name=model_name,
                        threshold=effective_threshold,
                    )
                    result["backend"] = "lancedb"
                    return result
            except Exception:  # noqa: BLE001 - use deterministic fallback below
                self._semantic_memory = None

        return {
            "strategy": "search",
            "results": self._keyword_schema_search(
                schema,
                query,
                limit=limit,
                model_name=model_name,
            ),
            "backend": "grep",
        }

    def recall(
        self,
        query: str,
        *,
        limit: int = 3,
        datasource: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            try:
                return self._get_index().search(
                    query,
                    limit=limit,
                    datasource=datasource,
                )
            except Exception:  # noqa: BLE001 - stale optional index fallback
                self._index = self._grep_index()
                return self._index.search(
                    query,
                    limit=limit,
                    datasource=datasource,
                )

    def store(
        self,
        nl: str,
        sql: str,
        *,
        datasource: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Persist a confirmed pair as Markdown, then refresh derived search."""

        if not nl.strip() or not sql.strip():
            raise ValueError("memory_store_requires_nl_and_sql")
        from wren.memory.markdown import write_query_markdown

        with self._lock:
            path = write_query_markdown(
                self.project_path,
                nl,
                sql,
                datasource=datasource,
                tags=tags,
                source="user",
            )
            rebuild = self._get_index().rebuild()
            return {
                "path": path.relative_to(self.project_path).as_posix(),
                "backend": rebuild.get("backend", getattr(self._get_index(), "name", "grep")),
                "query_pairs": int(rebuild.get("pairs", 0) or 0),
            }

    def _backend_name(self) -> str:
        try:
            return str(getattr(self._get_index(), "name", "grep"))
        except Exception:  # noqa: BLE001
            return "grep"

    def _grep_index(self) -> Any:
        from wren.memory.index_backend import get_index

        return get_index(self.project_path, str(self.memory_path), backend="grep")

    @staticmethod
    def _keyword_schema_search(
        schema: str,
        query: str,
        *,
        limit: int,
        model_name: str | None,
    ) -> list[dict[str, Any]]:
        tokens = {
            token
            for token in re.findall(r"[a-z0-9_]+", query.lower())
            if len(token) >= 2
        }
        chunks = [chunk.strip() for chunk in schema.split("\n\n") if chunk.strip()]
        scored: list[tuple[int, str]] = []
        for chunk in chunks:
            if model_name and model_name.lower() not in chunk.lower():
                continue
            score = sum(
                1
                for token in tokens
                if token in chunk.lower()
            )
            if score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [{"text": chunk, "score": score} for score, chunk in scored[:limit]]


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip().replace("\n", " ")
    return text[:500] or type(exc).__name__


__all__ = ["WrenMemoryService", "WrenMemoryStatus"]

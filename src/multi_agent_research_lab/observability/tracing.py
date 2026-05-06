"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from functools import lru_cache
import logging
import os
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)
_CURRENT_LANGSMITH_RUN_ID: ContextVar[UUID | None] = ContextVar(
    "current_langsmith_run_id", default=None
)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    The returned dict can be stored in ResearchState.trace or bridged to LangSmith,
    Langfuse, or OpenTelemetry in a production variant.
    """

    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    start_time = datetime.now(UTC)
    run_id = _start_langsmith_run(name, span["attributes"], start_time)
    token = _CURRENT_LANGSMITH_RUN_ID.set(run_id) if run_id else None
    error: str | None = None
    try:
        yield span
    except Exception as exc:
        error = str(exc)
        span["error"] = error
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
        if token is not None:
            _CURRENT_LANGSMITH_RUN_ID.reset(token)
        _finish_langsmith_run(run_id, span, error)


def flush_traces() -> None:
    """Flush buffered LangSmith traces before the CLI exits."""

    settings = get_settings()
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return
    try:
        from langsmith import Client
    except ImportError:
        return
    try:
        Client(
            api_key=settings.langsmith_api_key,
            api_url=settings.langsmith_endpoint,
        ).flush()
    except Exception as exc:
        logger.warning("Could not flush LangSmith traces: %s", exc)


def _start_langsmith_run(
    name: str, attributes: dict[str, Any], start_time: datetime
) -> UUID | None:
    settings = get_settings()
    if not settings.langsmith_tracing or not settings.langsmith_api_key:
        return None

    _configure_langsmith_environment(settings)
    try:
        run_id = uuid4()
        kwargs: dict[str, Any] = {
            "id": run_id,
            "start_time": start_time,
            "extra": {"metadata": {"lab": "multi-agent-research-lab"}},
        }
        parent_run_id = _CURRENT_LANGSMITH_RUN_ID.get()
        if parent_run_id is not None:
            kwargs["parent_run_id"] = parent_run_id
        _langsmith_client().create_run(
            name=name,
            run_type=_run_type_for(name),
            inputs={"attributes": attributes},
            project_name=settings.langsmith_project,
            **kwargs,
        )
        return run_id
    except Exception as exc:
        logger.warning("Could not create LangSmith run; keeping local trace only: %s", exc)
        return None


def _finish_langsmith_run(run_id: UUID | None, span: dict[str, Any], error: str | None) -> None:
    if run_id is None:
        return
    try:
        _langsmith_client().update_run(
            run_id,
            end_time=datetime.now(UTC),
            outputs={
                "duration_seconds": span["duration_seconds"],
                "attributes": span["attributes"],
            },
            error=error,
        )
    except Exception as exc:
        logger.warning("Could not update LangSmith run: %s", exc)


@lru_cache(maxsize=1)
def _langsmith_client() -> Any:
    settings = get_settings()
    try:
        from langsmith import Client
    except ImportError as exc:
        raise RuntimeError("langsmith package is not installed") from exc
    return Client(
        api_key=settings.langsmith_api_key,
        api_url=settings.langsmith_endpoint,
        auto_batch_tracing=False,
    )


def _configure_langsmith_environment(settings: Any) -> None:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key or "")
    os.environ.setdefault("LANGSMITH_ENDPOINT", settings.langsmith_endpoint)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)


def _run_type_for(name: str) -> str:
    if name in {"researcher", "analyst", "writer", "critic", "supervisor"}:
        return "tool"
    if "llm" in name:
        return "llm"
    return "chain"

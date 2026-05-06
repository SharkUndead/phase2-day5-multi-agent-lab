"""Benchmark skeleton for single-agent vs multi-agent."""

import re
from time import perf_counter
from typing import Any, Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, query: str, runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return practical lab metrics."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=_sum_cost(state),
        quality_score=_score_quality(state),
        citation_coverage=_citation_coverage(state),
        failure_rate=1.0 if state.errors else 0.0,
        notes=_summarize_notes(state),
    )
    return state, metrics


def _sum_cost(state: ResearchState) -> float | None:
    costs: list[float] = []
    for result in state.agent_results:
        value = result.metadata.get("cost_usd")
        if isinstance(value, (int, float)):
            costs.append(float(value))
    if not costs:
        return None
    return sum(costs)


def _score_quality(state: ResearchState) -> float:
    score = 0.0
    if state.final_answer:
        score += 3.0
    if state.sources:
        score += 2.0
    if state.research_notes:
        score += 1.5
    if state.analysis_notes:
        score += 1.5
    if _citation_coverage(state) >= 0.5:
        score += 1.0
    if state.errors:
        score -= 2.0
    return max(0.0, min(10.0, score))


def _citation_coverage(state: ResearchState) -> float:
    if not state.sources:
        return 0.0
    answer = state.final_answer or ""
    cited = {
        int(match)
        for match in re.findall(r"\[S(\d+)\]", answer)
        if 1 <= int(match) <= len(state.sources)
    }
    return len(cited) / len(state.sources)


def _summarize_notes(state: ResearchState) -> str:
    parts: list[str] = [
        f"sources={len(state.sources)}",
        f"iterations={state.iteration}",
        f"errors={len(state.errors)}",
    ]
    token_total = _sum_metadata_number(state, "input_tokens") + _sum_metadata_number(
        state, "output_tokens"
    )
    if token_total:
        parts.append(f"tokens~={int(token_total)}")
    return ", ".join(parts)


def _sum_metadata_number(state: ResearchState, key: str) -> float:
    total = 0.0
    for result in state.agent_results:
        value: Any = result.metadata.get(key)
        if isinstance(value, (int, float)):
            total += float(value)
    return total

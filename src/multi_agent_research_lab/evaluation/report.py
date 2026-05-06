"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown."""

    lines = [
        "# Benchmark Report",
        "",
        "## Summary Metrics",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Citation Coverage | Failure Rate | Notes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        citation = "" if item.citation_coverage is None else f"{item.citation_coverage:.0%}"
        failure = "" if item.failure_rate is None else f"{item.failure_rate:.0%}"
        lines.append(
            f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | "
            f"{citation} | {failure} | {item.notes} |"
        )
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- Quality is a lightweight heuristic for lab comparison; peer review should "
            "still score outputs.",
            "- Citation coverage counts source markers in the final answer, such as [S1].",
            "- Failure rate is 100% when a run records any workflow error.",
            "",
            "## Failure Mode Reflection",
            "",
            "Observed risk: provider calls, live search, or network access may fail "
            "during lab runs.",
            "",
            "Current fix: LLM and search clients use deterministic fallbacks, while the "
            "workflow records "
            "errors and stops via max-iteration guardrails. For production, add real trace links, "
            "stricter citation validation, and a human review step for low-confidence claims.",
        ]
    )
    return "\n".join(lines) + "\n"

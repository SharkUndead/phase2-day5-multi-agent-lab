"""Command-line entrypoint for the lab starter."""

import argparse
from collections.abc import Callable
from pathlib import Path
import sys
from typing import Annotated, Any

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
except ImportError:
    typer = None  # type: ignore[assignment]
    Console = None  # type: ignore[assignment,misc]
    Panel = None  # type: ignore[assignment,misc]

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.observability.tracing import flush_traces, trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

if typer is not None:
    app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
    console = Console()
else:
    app = None
    console = None


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


def _command(name: str | None = None) -> Callable[[Callable[..., None]], Callable[..., None]]:
    if app is None:
        return lambda function: function
    return app.command(name)


def _print_panel(content: object, title: str) -> None:
    if console is not None and Panel is not None:
        console.print(Panel.fit(content, title=title))
        return
    print(f"\n== {title} ==")
    print(content)


def _typer_option(*args: Any, **kwargs: Any) -> Any:
    if typer is None:
        return None
    return typer.Option(*args, **kwargs)


@_command()
def baseline(
    query: Annotated[str, _typer_option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline."""

    _init()
    try:
        state = _run_baseline(query)
        _print_panel(state.final_answer, "Single-Agent Baseline")
    finally:
        flush_traces()


@_command("multi-agent")
def multi_agent(
    query: Annotated[str, _typer_option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    try:
        state = ResearchState(request=ResearchQuery(query=query))
        workflow = MultiAgentWorkflow()
        result = workflow.run(state)
        if console is not None:
            console.print(result.model_dump_json(indent=2))
        else:
            print(result.model_dump_json(indent=2))
    finally:
        flush_traces()


@_command()
def benchmark(
    query: Annotated[
        str,
        _typer_option(
            "--query",
            "-q",
            help="Research query used for both baseline and multi-agent runs",
        ),
    ] = "Research GraphRAG state-of-the-art and write a 500-word summary",
    output: Annotated[
        Path,
        _typer_option("--output", "-o", help="Markdown report path under reports/"),
    ] = Path("benchmark_report.md"),
) -> None:
    """Run baseline and multi-agent once, then write a markdown benchmark report."""

    _init()
    try:
        _, baseline_metrics = run_benchmark("baseline", query, _run_baseline)
        _, multi_metrics = run_benchmark("multi-agent", query, _run_multi_agent)
        report = render_markdown_report([baseline_metrics, multi_metrics])
        path = LocalArtifactStore().write_text(str(output), report)
        _print_panel(report, f"Benchmark written to {path}")
    finally:
        flush_traces()


def _run_baseline(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    with trace_span("single_agent_baseline", {"query": request.query}) as span:
        response = LLMClient().complete(
            system_prompt=(
                "You are a single-agent research assistant. Do research planning, analysis, "
                "and writing in one response. Be concise and mention limitations."
            ),
            user_prompt=(
                f"Question: {request.query}\n"
                f"Audience: {request.audience}\n\n"
                "Write the final answer with a summary, key points, and caveats."
            ),
        )
    state.final_answer = response.content
    state.agent_results.append(
        AgentResult(
            agent=AgentName.BASELINE,
            content=response.content,
            metadata={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            },
        )
    )
    state.add_trace_event("baseline.complete", {**span, "answer_chars": len(response.content)})
    return state


def _run_multi_agent(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    return MultiAgentWorkflow().run(state)


def _main() -> None:
    if app is not None:
        app()
        return

    parser = argparse.ArgumentParser(description="Multi-Agent Research Lab starter CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline_parser = subparsers.add_parser("baseline")
    baseline_parser.add_argument("--query", "-q", required=True)

    multi_parser = subparsers.add_parser("multi-agent")
    multi_parser.add_argument("--query", "-q", required=True)

    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_parser.add_argument(
        "--query",
        "-q",
        default="Research GraphRAG state-of-the-art and write a 500-word summary",
    )
    benchmark_parser.add_argument("--output", "-o", default="benchmark_report.md")

    args = parser.parse_args()
    if args.command == "baseline":
        baseline(query=args.query)
    elif args.command == "multi-agent":
        multi_agent(query=args.query)
    elif args.command == "benchmark":
        benchmark(query=args.query, output=Path(args.output))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    _main()

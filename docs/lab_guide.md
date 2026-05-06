# Lab Guide: Multi-Agent Research System

## Scenario

Build a research assistant that can receive a long-form question, gather source material,
analyze evidence, and write a final answer. The lab compares two approaches:

1. Single-agent baseline: one agent handles the whole task.
2. Multi-agent workflow: Supervisor coordinates Researcher, Analyst, and Writer.

## Rules

- Do not add agents without a clear reason.
- Give each agent one focused responsibility.
- Keep shared state explicit enough for debugging and peer review.
- Trace every major step.
- Benchmark the two approaches with concrete metrics.

## Milestone 1: Baseline

Suggested files:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

Implemented: the baseline command now calls `LLMClient`, stores the final answer, and records
a trace event. If `OPENAI_API_KEY` is missing, it uses the offline fallback.

## Milestone 2: Supervisor

Suggested files:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

Implemented routing policy:

- Researcher runs when sources or research notes are missing.
- Analyst runs when analysis notes are missing.
- Writer runs when the final answer is missing.
- The workflow stops when final answer exists or max iterations is reached.

## Milestone 3: Worker Agents

Suggested files:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

Implemented workers:

- Researcher searches, deduplicates sources, and writes source-backed notes.
- Analyst structures claims, evidence, trade-offs, and open questions.
- Writer synthesizes the final answer with source references.

## Milestone 4: Trace And Benchmark

Suggested files:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark metrics:

| Metric | How it is measured |
|---|---|
| Latency | Wall-clock time |
| Cost | Provider metadata when available |
| Quality | Lightweight heuristic plus peer review |
| Citation coverage | Referenced sources divided by total sources |
| Failure rate | Whether the run recorded workflow errors |

Run:

```bash
python -m multi_agent_research_lab.cli benchmark
```

The report is written to `reports/benchmark_report.md`.

## Exit Ticket

1. Use multi-agent workflows when task complexity benefits from clear role separation,
   source checking, and traceable handoffs.
2. Avoid multi-agent workflows when the task is simple, latency-sensitive, or does not need
   explicit intermediate reasoning.

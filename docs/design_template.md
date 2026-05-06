# Design Template

## Problem

Build a research assistant that receives a long-form question, gathers relevant sources,
extracts evidence, analyzes the trade-offs, and writes a final answer for technical learners.

## Why multi-agent?

A single agent can answer quickly, but it mixes searching, reasoning, and writing in one
opaque step. The multi-agent workflow improves traceability: each role has a focused output,
the shared state shows handoffs, and benchmark metrics make the trade-off between quality
and latency visible.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Select the next worker and stop condition | Shared `ResearchState` | Route: `researcher`, `analyst`, `writer`, or `done` | Looping, wrong route, max-iteration stop |
| Researcher | Find and summarize sources | Query and max source count | `sources`, `research_notes` | Weak source coverage, search provider failure |
| Analyst | Turn notes into structured insights | Research notes and sources | `analysis_notes` | Shallow reasoning, missing uncertainty |
| Writer | Synthesize a final answer | Query, notes, analysis, sources | `final_answer` | Missing citations, vague answer |
| Critic | Optional validation pass | Final answer and sources | Citation coverage findings | Overly simple fact-checking |

## Shared state

- `request`: original query, audience, and max source count.
- `iteration`: guardrail for stopping the workflow.
- `route_history`: explains which agent ran and in what order.
- `sources`: source documents for citation and evidence.
- `research_notes`: source-grounded notes from the researcher.
- `analysis_notes`: claims, trade-offs, and uncertainty from the analyst.
- `final_answer`: user-facing answer from the writer.
- `agent_results`: per-agent outputs and metadata such as tokens and cost.
- `trace`: lightweight span events for debugging and review.
- `errors`: recoverable failures or guardrail stops.

## Routing policy

```text
supervisor
  -> researcher if sources or research_notes are missing
  -> analyst if analysis_notes are missing
  -> writer if final_answer is missing
  -> done when final_answer exists or max_iterations is reached
```

Each worker returns control to the supervisor. The default happy path is:

```text
supervisor -> researcher -> supervisor -> analyst -> supervisor -> writer -> supervisor -> done
```

## Guardrails

- Max iterations: `MAX_ITERATIONS`, default `6`.
- Timeout: provider clients use `TIMEOUT_SECONDS`, default `60`.
- Retry: `LLMClient.complete` retries provider calls up to three times.
- Fallback: LLM and search clients provide deterministic offline fallback outputs.
- Validation: workflow records unknown routes, worker failures, and max-iteration exits.

## Benchmark plan

| Query | Metric | Expected outcome |
|---|---|---|
| Research GraphRAG state-of-the-art and write a 500-word summary | Latency, quality, citation coverage | Multi-agent should be slower but more traceable |
| Compare single-agent and multi-agent workflows for customer support | Quality, failure rate | Multi-agent should expose role-specific reasoning |
| Summarize production guardrails for LLM agents | Citation coverage, quality | Multi-agent should cite sources and mention trade-offs |

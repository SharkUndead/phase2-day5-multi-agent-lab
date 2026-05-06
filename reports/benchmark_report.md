# Benchmark Report

## Summary Metrics

| Run | Latency (s) | Cost (USD) | Quality | Citation Coverage | Failure Rate | Notes |
|---|---:|---:|---:|---:|---:|---|
| baseline | 10.45 |  | 3.0 | 0% | 0% | sources=0, iterations=0, errors=0, tokens~=651 |
| multi-agent | 92.03 |  | 9.0 | 100% | 0% | sources=5, iterations=4, errors=0, tokens~=3339 |

## Review Notes

- Quality is a lightweight heuristic for lab comparison; peer review should still score outputs.
- Citation coverage counts source markers in the final answer, such as [S1].
- Failure rate is 100% when a run records any workflow error.

## Failure Mode Reflection

Observed risk: provider calls, live search, or network access may fail during lab runs.

Current fix: LLM and search clients use deterministic fallbacks, while the workflow records errors and stops via max-iteration guardrails. For production, add real trace links, stricter citation validation, and a human review step for low-confidence claims.

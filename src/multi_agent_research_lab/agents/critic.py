"""Optional critic agent skeleton for bonus work."""

import re

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate citation coverage and append findings."""

        with trace_span(self.name, {"source_count": len(state.sources)}) as span:
            answer = state.final_answer or ""
            cited = {
                int(match)
                for match in re.findall(r"\[S(\d+)\]", answer)
                if 1 <= int(match) <= len(state.sources)
            }
            coverage = 0.0 if not state.sources else len(cited) / len(state.sources)
            findings: list[str] = [f"Citation coverage: {coverage:.0%}."]
            if not answer.strip():
                findings.append("Final answer is missing.")
            if state.sources and coverage == 0:
                findings.append("No source markers were found in the final answer.")
            if state.errors:
                findings.append(f"Workflow recorded {len(state.errors)} error(s).")
            content = "\n".join(f"- {finding}" for finding in findings)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.CRITIC,
                    content=content,
                    metadata={"citation_coverage": coverage},
                )
            )

        state.add_trace_event("agent.critic", {**span, "citation_coverage": coverage})
        return state

"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        The analyst should reason over notes rather than search or write the final answer.
        """

        with trace_span(self.name, {"source_count": len(state.sources)}) as span:
            source_titles = "\n".join(
                f"[S{index}] {source.title}" for index, source in enumerate(state.sources, start=1)
            )
            response = LLMClient().complete(
                system_prompt=(
                    "You are an analyst agent. Turn research notes into structured "
                    "insights, compare viewpoints, identify weak evidence, and keep "
                    "citations like [S1]."
                ),
                user_prompt=(
                    f"Question: {state.request.query}\n\n"
                    f"Research notes:\n{state.research_notes or 'No research notes.'}\n\n"
                    f"Available sources:\n{source_titles}\n\n"
                    "Return sections: Key claims, Evidence strength, Trade-offs, "
                    "Open questions."
                ),
            )
            state.analysis_notes = self._normalize_analysis(response.content)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=state.analysis_notes,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )

        state.add_trace_event(
            "agent.analyst",
            {
                **span,
                "analysis_chars": len(state.analysis_notes or ""),
            },
        )
        return state

    def _normalize_analysis(self, content: str) -> str:
        stripped = content.strip()
        if not stripped:
            return (
                "Key claims:\n"
                "- The query needs source-grounded synthesis before final writing.\n\n"
                "Evidence strength:\n"
                "- Current evidence is limited; verify citations before submission.\n\n"
                "Trade-offs:\n"
                "- Multi-agent workflow improves traceability but adds latency.\n\n"
                "Open questions:\n"
                "- Which claims require fresher or domain-specific sources?"
            )
        required_sections = [
            "Key claims",
            "Evidence strength",
            "Trade-offs",
            "Open questions",
        ]
        missing = [
            section
            for section in required_sections
            if section.lower() not in stripped.lower()
        ]
        if missing:
            checklist = "\n".join(f"- {section}" for section in missing)
            stripped += f"\n\nAnalyst checklist:\n{checklist}"
        return stripped

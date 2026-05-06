"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Routes are intentionally deterministic so the trace is easy to explain during
        peer review.
        """

        with trace_span(self.name, {"iteration": state.iteration}) as span:
            settings = get_settings()
            if state.iteration >= settings.max_iterations:
                route = "done"
                state.errors.append(
                    f"Stopped after reaching max_iterations={settings.max_iterations}."
                )
            elif not state.sources or not state.research_notes:
                route = "researcher"
            elif not state.analysis_notes:
                route = "analyst"
            elif not state.final_answer:
                route = "writer"
            else:
                route = "done"

            state.record_route(route)
            state.add_trace_event(
                "supervisor.route",
                {
                    **span,
                    "route": route,
                    "iteration": state.iteration,
                    "has_sources": bool(state.sources),
                    "has_research_notes": bool(state.research_notes),
                    "has_analysis_notes": bool(state.analysis_notes),
                    "has_final_answer": bool(state.final_answer),
                },
            )
        return state

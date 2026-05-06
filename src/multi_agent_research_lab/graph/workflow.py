"""LangGraph workflow skeleton."""

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.agents: dict[str, BaseAgent] = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }

    def build(self) -> object:
        """Return a serializable description of the workflow graph.

        The lab can swap this for a real LangGraph `StateGraph` when the optional
        dependency is installed. The runtime semantics mirror the target graph:
        supervisor chooses one worker, then control returns to supervisor.
        """

        return {
            "nodes": ["supervisor", *self.agents.keys(), "done"],
            "edges": {
                "supervisor": ["researcher", "analyst", "writer", "done"],
                "researcher": ["supervisor"],
                "analyst": ["supervisor"],
                "writer": ["supervisor"],
            },
        }

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        Guardrails live at orchestration level: max iterations, unknown-route validation,
        and worker failure fallback.
        """

        with trace_span("multi_agent_workflow", {"query": state.request.query}) as span:
            settings = get_settings()
            state.add_trace_event("workflow.start", span)

            for _ in range(settings.max_iterations + 1):
                state = self.supervisor.run(state)
                route = state.route_history[-1]
                if route == "done":
                    state.add_trace_event("workflow.done", {"iterations": state.iteration})
                    return state

                agent = self.agents.get(route)
                if agent is None:
                    state.errors.append(f"Supervisor selected unknown route: {route}")
                    state.record_route("done")
                    state.add_trace_event("workflow.done", {"reason": "unknown_route"})
                    return state

                try:
                    state = agent.run(state)
                except Exception as exc:
                    state.errors.append(f"{route} failed: {exc}")
                    if route != "writer":
                        try:
                            state = self.agents["writer"].run(state)
                        except Exception as writer_exc:
                            raise AgentExecutionError(
                                f"{route} failed and writer fallback failed: {writer_exc}"
                            ) from writer_exc
                    state.record_route("done")
                    state.add_trace_event("workflow.done", {"reason": "agent_failure"})
                    return state

            state.errors.append(f"Workflow exceeded max_iterations={settings.max_iterations}.")
            state.record_route("done")
            state.add_trace_event("workflow.done", {"reason": "max_iterations"})
        return state

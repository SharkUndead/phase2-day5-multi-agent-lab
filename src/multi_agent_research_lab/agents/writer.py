"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        The final answer should be readable and traceable back to the source list.
        """

        with trace_span(self.name, {"audience": state.request.audience}) as span:
            source_block = "\n".join(
                f"[S{index}] {source.title} - {source.url or 'n/a'}"
                for index, source in enumerate(state.sources, start=1)
            )
            response = LLMClient().complete(
                system_prompt=(
                    "You are a writer agent. Produce a clear final research answer for "
                    "the requested audience. Use source references like [S1]."
                ),
                user_prompt=(
                    f"Question: {state.request.query}\n\n"
                    f"Audience: {state.request.audience}\n\n"
                    f"Research notes:\n{state.research_notes or 'No research notes.'}\n\n"
                    f"Analysis notes:\n{state.analysis_notes or 'No analysis notes.'}\n\n"
                    f"Sources:\n{source_block}\n\n"
                    "Write the final answer with: Summary, Key points, Caveats, Sources."
                ),
            )
            state.final_answer = self._finalize(response.content, source_block)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=state.final_answer,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )

        state.add_trace_event(
            "agent.writer",
            {
                **span,
                "answer_chars": len(state.final_answer or ""),
            },
        )
        return state

    def _finalize(self, content: str, source_block: str) -> str:
        stripped = content.strip()
        if not stripped:
            stripped = (
                "Summary\n"
                "The available research supports a cautious, source-grounded answer.\n\n"
                "Key points\n"
                "- Review the collected sources before making strong claims.\n\n"
                "Caveats\n"
                "- The result may rely on fallback data when live providers are not configured."
            )
        if "Sources" not in stripped:
            stripped += "\n\nSources\n" + source_block
        elif source_block and "[S1]" not in stripped:
            stripped += "\n\nSource references\n" + source_block
        return stripped

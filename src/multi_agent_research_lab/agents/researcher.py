"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Search is isolated in SearchClient, so this agent focuses on source filtering and
        concise note generation.
        """

        with trace_span(self.name, {"query": state.request.query}) as span:
            sources = SearchClient().search(state.request.query, state.request.max_sources)
            state.sources = self._deduplicate_sources(sources)[: state.request.max_sources]
            source_block = self._format_sources(state.sources)
            response = LLMClient().complete(
                system_prompt=(
                    "You are a research agent. Extract concise, source-grounded notes. "
                    "Prefer factual bullets and cite sources as [S1], [S2]."
                ),
                user_prompt=(
                    f"Question: {state.request.query}\n\n"
                    f"Audience: {state.request.audience}\n\n"
                    f"Sources:\n{source_block}\n\n"
                    "Write research notes with 4-6 bullets."
                ),
            )
            state.research_notes = self._ensure_citations(response.content, state.sources)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=state.research_notes,
                    metadata={
                        "source_count": len(state.sources),
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )

        state.add_trace_event(
            "agent.researcher",
            {
                **span,
                "source_count": len(state.sources),
                "note_chars": len(state.research_notes or ""),
            },
        )
        return state

    def _deduplicate_sources(self, sources: list[SourceDocument]) -> list[SourceDocument]:
        seen: set[str] = set()
        deduped: list[SourceDocument] = []
        for source in sources:
            key = source.url or source.title
            if key in seen:
                continue
            seen.add(key)
            deduped.append(source)
        return deduped

    def _format_sources(self, sources: list[SourceDocument]) -> str:
        return "\n".join(
            f"[S{index}] {source.title}\nURL: {source.url or 'n/a'}\nSnippet: {source.snippet}"
            for index, source in enumerate(sources, start=1)
        )

    def _ensure_citations(self, content: str, sources: list[SourceDocument]) -> str:
        stripped = content.strip()
        if not stripped:
            stripped = "\n".join(
                f"- [S{index}] {source.title}: {source.snippet}"
                for index, source in enumerate(sources, start=1)
            )
        if sources and "[S1]" not in stripped:
            source_list = "\n".join(
                f"- [S{index}] {source.title}: {source.snippet}"
                for index, source in enumerate(sources, start=1)
            )
            stripped = f"{stripped}\n\nSource-backed notes:\n{source_list}"
        return stripped

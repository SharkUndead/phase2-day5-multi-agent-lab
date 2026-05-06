from pytest import MonkeyPatch

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def _force_offline(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("MALAB_DOTENV_OVERRIDE", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    get_settings.cache_clear()


def test_supervisor_routes_to_researcher_first_offline(monkeypatch: MonkeyPatch) -> None:
    _force_offline(monkeypatch)
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "researcher"


def test_worker_agents_populate_state(monkeypatch: MonkeyPatch) -> None:
    _force_offline(monkeypatch)

    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    state = ResearcherAgent().run(state)
    state = AnalystAgent().run(state)
    state = WriterAgent().run(state)

    assert state.sources
    assert state.research_notes
    assert state.analysis_notes
    assert state.final_answer
    assert state.agent_results


def test_workflow_reaches_done(monkeypatch: MonkeyPatch) -> None:
    _force_offline(monkeypatch)

    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = MultiAgentWorkflow().run(state)

    assert result.route_history[-1] == "done"
    assert result.final_answer
    assert not result.errors

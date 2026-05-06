"""Search client abstraction for ResearcherAgent."""

import json
import logging
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Uses Tavily when `TAVILY_API_KEY` is configured. Otherwise, returns a small
        deterministic source set so ResearcherAgent can be developed without network access.
        """

        settings = get_settings()
        max_results = max(1, min(max_results, 20))
        if not settings.tavily_api_key:
            logger.info("TAVILY_API_KEY is not configured; using mock search results.")
            return self._mock_search(query, max_results)

        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": "basic",
            "include_answer": False,
        }
        request = Request(
            "https://api.tavily.com/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=settings.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as exc:
            logger.warning("Tavily search failed; using mock search results: %s", exc)
            return self._mock_search(query, max_results)

        results = data.get("results", [])
        documents: list[SourceDocument] = []
        for item in results[:max_results]:
            if not isinstance(item, dict):
                continue
            documents.append(
                SourceDocument(
                    title=str(item.get("title") or "Untitled source"),
                    url=self._optional_str(item.get("url")),
                    snippet=str(item.get("content") or item.get("snippet") or ""),
                    metadata={"score": item.get("score"), "provider": "tavily"},
                )
            )
        return documents or self._mock_search(query, max_results)

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        encoded_query = urlencode({"q": query})
        templates = [
            (
                "Architecture overview",
                "Breaks the problem into role design, shared state, orchestration, and "
                "evaluation criteria.",
            ),
            (
                "Implementation guide",
                "Highlights provider abstraction, retry behavior, deterministic fallbacks, "
                "and typed schemas.",
            ),
            (
                "Evaluation note",
                "Discusses latency, estimated cost, quality review, citation coverage, "
                "and failure rate.",
            ),
            (
                "Production guardrails",
                "Summarizes max iterations, timeout controls, validation, and traceability.",
            ),
            (
                "Failure mode catalog",
                "Lists stale sources, missing citations, weak evidence, and retry exhaustion.",
            ),
        ]
        return [
            SourceDocument(
                title=f"{title}: {query}",
                url=f"https://example.com/search?{encoded_query}&source={index}",
                snippet=snippet,
                metadata={"provider": "mock", "rank": index},
            )
            for index, (title, snippet) in enumerate(templates[:max_results], start=1)
        ]

    @staticmethod
    def _optional_str(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

import logging
from dataclasses import dataclass
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from multi_agent_research_lab.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Uses OpenAI when `OPENAI_API_KEY` is configured. Without a key, the client returns
        a deterministic offline response so the lab can still run smoke tests and demos.
        """

        settings = get_settings()
        if not settings.openai_api_key:
            logger.info("OPENAI_API_KEY is not configured; using offline LLM fallback.")
            return self._offline_complete(system_prompt, user_prompt)

        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("openai package is not installed; using offline LLM fallback.")
            return self._offline_complete(system_prompt, user_prompt)

        try:
            return self._openai_complete(OpenAI, system_prompt, user_prompt)
        except Exception as exc:
            logger.warning("OpenAI completion failed; using offline LLM fallback: %s", exc)
            return self._offline_complete(system_prompt, user_prompt)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.2, min=0.2, max=1))
    def _openai_complete(
        self, openai_client: type[Any], system_prompt: str, user_prompt: str
    ) -> LLMResponse:
        settings = get_settings()
        client = openai_client(
            api_key=settings.openai_api_key,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        return LLMResponse(
            content=content.strip(),
            input_tokens=None if usage is None else usage.prompt_tokens,
            output_tokens=None if usage is None else usage.completion_tokens,
            cost_usd=None,
        )

    def _offline_complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        system_hint = self._compact(system_prompt, 220)
        user_hint = self._compact(user_prompt, 900)
        content = (
            "Offline LLM fallback response\n\n"
            f"System intent: {system_hint}\n\n"
            f"Draft based on prompt: {user_hint}\n\n"
            "Use this as a smoke-test output. Configure OPENAI_API_KEY for provider-backed "
            "reasoning and better quality."
        )
        approx_input = max(1, (len(system_prompt) + len(user_prompt)) // 4)
        approx_output = max(1, len(content) // 4)
        return LLMResponse(content=content, input_tokens=approx_input, output_tokens=approx_output)

    @staticmethod
    def _compact(text: str, max_chars: int) -> str:
        normalized = " ".join(text.split())
        if len(normalized) <= max_chars:
            return normalized
        return normalized[: max_chars - 3] + "..."

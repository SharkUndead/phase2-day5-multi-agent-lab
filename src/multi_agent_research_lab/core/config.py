"""Application configuration.

Keep config small and explicit. Do not read environment variables directly in agents.
"""

from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

_ENV_LOADED = False


class Settings(BaseModel):
    """Runtime settings loaded from environment variables or `.env`."""

    model_config = ConfigDict(extra="ignore")

    app_env: str = Field(default_factory=lambda: _env("APP_ENV", "local"))
    log_level: str = Field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))

    openai_api_key: str | None = Field(default_factory=lambda: _env_optional("OPENAI_API_KEY"))
    openai_model: str = Field(default_factory=lambda: _env("OPENAI_MODEL", "gpt-4o-mini"))

    langsmith_api_key: str | None = Field(
        default_factory=lambda: _env_optional("LANGSMITH_API_KEY")
    )
    langsmith_tracing: bool = Field(default_factory=lambda: _env_bool("LANGSMITH_TRACING", False))
    langsmith_endpoint: str = Field(
        default_factory=lambda: _env("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    )
    langsmith_project: str = Field(
        default_factory=lambda: _env("LANGSMITH_PROJECT", "multi-agent-research-lab")
    )

    tavily_api_key: str | None = Field(default_factory=lambda: _env_optional("TAVILY_API_KEY"))

    max_iterations: int = Field(default_factory=lambda: _env_int("MAX_ITERATIONS", 6), ge=1, le=20)
    timeout_seconds: int = Field(
        default_factory=lambda: _env_int("TIMEOUT_SECONDS", 60), ge=5, le=600
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


def _env(name: str, default: str) -> str:
    _load_dotenv()
    return os.environ.get(name, default)


def _env_optional(name: str) -> str | None:
    value = _env(name, "").strip()
    return value or None


def _env_int(name: str, default: int) -> int:
    value = _env(name, str(default)).strip()
    try:
        return int(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = _env(name, str(default)).strip().lower()
    return value in {"1", "true", "yes", "on"}


def _load_dotenv() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    path = Path(".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        normalized_key = key.strip()
        normalized_value = value.strip().strip('"').strip("'")
        if os.environ.get("MALAB_DOTENV_OVERRIDE", "true").lower() in {"1", "true", "yes", "on"}:
            os.environ[normalized_key] = normalized_value
        else:
            os.environ.setdefault(normalized_key, normalized_value)

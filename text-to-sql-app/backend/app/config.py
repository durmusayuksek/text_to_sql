import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv(override=True)


class ConfigurationError(RuntimeError):
    pass


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer.") from exc


def _get_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    normalized = raw_value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ConfigurationError(f"{name} must be a boolean.")


@dataclass(frozen=True)
class Settings:
    app_name: str = "Text to SQL App"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"

    openai_api_key: str | None = None
    agent_mode: str | None = None  # "mock" or "openai"
    query_agent_mode: str | None = None  # Backward-compatible alias.
    openai_model: str = "gpt-4.1-mini"
    openai_timeout_seconds: int = 30
    debug_query_results: bool = False
    response_agent_max_sample_rows: int = 5

    def __post_init__(self) -> None:
        mode = (self.agent_mode or self.query_agent_mode or "mock").lower()
        object.__setattr__(self, "agent_mode", mode)
        object.__setattr__(self, "query_agent_mode", mode)


@lru_cache
def get_settings() -> Settings:
    settings = Settings(
        app_name=os.getenv("APP_NAME", "Text to SQL App"),
        app_env=os.getenv("APP_ENV", "development"),
        frontend_origin=os.getenv(
            "FRONTEND_ORIGIN",
            "http://localhost:5173",
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        agent_mode=(
            os.getenv("AGENT_MODE")
            or os.getenv("QUERY_AGENT_MODE")
            or "mock"
        ).lower(),
        openai_model=os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini",
        ),
        openai_timeout_seconds=_get_int_env(
            "OPENAI_TIMEOUT_SECONDS",
            30,
        ),
        debug_query_results=_get_bool_env(
            "DEBUG_QUERY_RESULTS",
            False,
        ),
        response_agent_max_sample_rows=_get_int_env(
            "RESPONSE_AGENT_MAX_SAMPLE_ROWS",
            5,
        ),
    )

    validate_settings(settings)

    return settings


def refresh_settings() -> Settings:
    load_dotenv(override=True)
    get_settings.cache_clear()
    return get_settings()


def validate_settings(settings: Settings) -> None:
    if settings.agent_mode not in {"mock", "openai"}:
        raise ConfigurationError("AGENT_MODE must be either 'mock' or 'openai'.")

    if settings.agent_mode == "openai" and not settings.openai_api_key:
        raise ConfigurationError("OPENAI_API_KEY is required when AGENT_MODE=openai.")

    if settings.openai_timeout_seconds <= 0:
        raise ConfigurationError("OPENAI_TIMEOUT_SECONDS must be greater than 0.")

    if settings.response_agent_max_sample_rows < 0:
        raise ConfigurationError("RESPONSE_AGENT_MAX_SAMPLE_ROWS cannot be negative.")

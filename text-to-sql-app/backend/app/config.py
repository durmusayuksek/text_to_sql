import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Text to SQL App"
    app_env: str = "development"
    frontend_origin: str = "http://localhost:5173"
    openai_api_key: str | None = None
    query_agent_mode: str = "mock"
    openai_model: str = "gpt-4.1-mini"


@lru_cache
def get_settings() -> Settings:
    settings = Settings(
        app_name=os.getenv("APP_NAME", "Text to SQL App"),
        app_env=os.getenv("APP_ENV", "development"),
        frontend_origin=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        query_agent_mode=os.getenv("QUERY_AGENT_MODE", "mock").lower(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    if settings.query_agent_mode not in {"mock", "openai"}:
        raise ConfigurationError("QUERY_AGENT_MODE must be either 'mock' or 'openai'.")

    if settings.query_agent_mode == "openai" and not settings.openai_api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY is required when QUERY_AGENT_MODE=openai."
        )

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    app_name: str = Field(serialization_alias="appName")
    status: Literal["ok"]
    environment: str


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sql: str
    explanation: str
    data: list[dict[str, Any]]
    query_agent_mode: Literal["mock", "openai"]

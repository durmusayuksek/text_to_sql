from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    app_name: str = Field(serialization_alias="appName")
    status: Literal["ok"]
    environment: str


class AskRequest(BaseModel):
    question: str


class GeneratedSqlQuery(BaseModel):
    query_id: str
    purpose: str
    sql: str


class QueryResult(BaseModel):
    query_id: str
    purpose: str
    sql: str
    rows: list[dict[str, Any]]
    warnings: list[str] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    key_findings: list[str]
    assumptions: list[str]
    limitations: list[str]
    confidence: Literal["high", "medium", "low"]
    generated_sql_queries: list[GeneratedSqlQuery]
    query_results: list[QueryResult] | None = None
    query_agent_mode: Literal["mock", "openai"]

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.agents import openai_client
from app.catalog import build_catalog_context
from app.config import get_settings

Confidence = Literal["high", "medium", "low"]
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "query_agent.md"


@dataclass(frozen=True)
class QueryAgentResult:
    sql: str
    explanation: str
    confidence: Confidence
    assumptions: list[str]
    schema_context_used: str


class QueryAgentError(RuntimeError):
    pass


class QueryAgentResponseError(QueryAgentError):
    pass


class QueryAgentLowConfidenceError(QueryAgentError):
    pass


def generate_sql(question: str) -> QueryAgentResult:
    """Generate SQL from catalog metadata without reading Parquet data."""
    settings = get_settings()
    schema_context = build_catalog_context()

    if settings.query_agent_mode == "openai":
        return generate_openai_sql(question, schema_context)

    return QueryAgentResult(
        sql=get_mock_sql(question),
        explanation="This mocked query returns sample rows from the central data catalog.",
        confidence="high",
        assumptions=[],
        schema_context_used=schema_context,
    )


def generate_openai_sql(
    question: str,
    schema_context: str,
) -> QueryAgentResult:
    raw_response = openai_client.create_chat_completion(
        build_openai_messages(question, schema_context)
    )
    result = parse_query_agent_response(raw_response, schema_context_used=schema_context)

    if result.confidence == "low":
        raise QueryAgentLowConfidenceError(
            "Query Agent returned low confidence SQL. Please rephrase the question or add metadata."
        )

    return result


def build_openai_messages(
    question: str,
    schema_context: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": load_query_agent_prompt(),
        },
        {
            "role": "user",
            "content": (
                f"User question:\n{question}\n\n"
                f"Data catalog metadata:\n{schema_context}"
            ),
        },
    ]


def load_query_agent_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def parse_query_agent_response(
    raw_response: str,
    schema_context_used: str = "",
) -> QueryAgentResult:
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise QueryAgentResponseError("Query Agent response is not valid JSON.") from error

    if not isinstance(payload, dict):
        raise QueryAgentResponseError("Query Agent response must be a JSON object.")

    sql = require_string(payload, "sql")
    if not sql.strip():
        raise QueryAgentResponseError("Query Agent response is missing sql.")

    explanation = require_string(payload, "explanation")
    confidence = require_confidence(payload)
    assumptions = require_assumptions(payload)

    return QueryAgentResult(
        sql=sql.strip(),
        explanation=explanation.strip(),
        confidence=confidence,
        assumptions=assumptions,
        schema_context_used=schema_context_used,
    )


def require_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)

    if not isinstance(value, str):
        raise QueryAgentResponseError(f"Query Agent response field '{field_name}' must be a string.")

    return value


def require_confidence(payload: dict[str, Any]) -> Confidence:
    value = payload.get("confidence")

    if value not in {"high", "medium", "low"}:
        raise QueryAgentResponseError(
            "Query Agent response field 'confidence' must be high, medium, or low."
        )

    return value


def require_assumptions(payload: dict[str, Any]) -> list[str]:
    value = payload.get("assumptions")

    if not isinstance(value, list):
        raise QueryAgentResponseError("Query Agent response field 'assumptions' must be a list.")

    if not all(isinstance(item, str) for item in value):
        raise QueryAgentResponseError(
            "Query Agent response field 'assumptions' must contain only strings."
        )

    return value


def get_mock_sql(question: str) -> str:
    lowered_question = question.lower()

    if "passenger" in lowered_question or "pax" in lowered_question:
        return (
            "SELECT route, SUM(forecast_pax) AS forecast_passengers "
            "FROM pax_forecast "
            "GROUP BY route "
            "ORDER BY forecast_passengers DESC "
            "LIMIT 10"
        )

    if "margin" in lowered_question or "profit" in lowered_question:
        return (
            "SELECT event_name, ticket_revenue, entertainment_cost, margin "
            "FROM special_cruise_profit "
            "ORDER BY margin DESC "
            "LIMIT 10"
        )

    return "SELECT * FROM qa LIMIT 10"

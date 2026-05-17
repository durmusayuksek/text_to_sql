import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.agents import openai_client
from app.agents.analysis_planner import AnalysisPlannerResult
from app.agents.query_agent import QueryAgentResult, query_agent_result_to_dict
from app.config import get_settings
from app.duckdb_layer.query_runner import QueryExecutionResult

Confidence = Literal["high", "medium", "low"]
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "response_agent.md"


@dataclass(frozen=True)
class ResponseAgentResult:
    answer: str
    key_findings: list[str]
    assumptions: list[str]
    limitations: list[str]
    confidence: Confidence


class ResponseAgentError(RuntimeError):
    pass


class ResponseAgentResponseError(ResponseAgentError):
    pass


def generate_response(
    question: str,
    plan: AnalysisPlannerResult,
    query_agent_result: QueryAgentResult,
    query_results: list[QueryExecutionResult],
) -> ResponseAgentResult:
    settings = get_settings()

    if settings.query_agent_mode == "openai":
        raw_response = openai_client.create_chat_completion(
            build_openai_messages(question, plan, query_agent_result, query_results)
        )
        return parse_response_agent_response(raw_response)

    return build_mock_response(plan, query_results)


def build_openai_messages(
    question: str,
    plan: AnalysisPlannerResult,
    query_agent_result: QueryAgentResult,
    query_results: list[QueryExecutionResult],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": load_response_agent_prompt(),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "question": question,
                    "planner_output": plan.to_prompt_payload(),
                    "query_agent_output": query_agent_result_to_dict(query_agent_result),
                    "query_results": [
                        query_result.to_response_payload() for query_result in query_results
                    ],
                },
                indent=2,
                default=str,
            ),
        },
    ]


def load_response_agent_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_mock_response(
    plan: AnalysisPlannerResult,
    query_results: list[QueryExecutionResult],
) -> ResponseAgentResult:
    total_rows = sum(len(result.rows) for result in query_results)
    row_label = "row" if total_rows == 1 else "rows"
    query_label = "query" if len(query_results) == 1 else "queries"

    key_findings = [
        f"{result.query_id} returned {len(result.rows)} rows for: {result.purpose}"
        for result in query_results
    ]

    return ResponseAgentResult(
        answer=(
            f"I ran {len(query_results)} validated {query_label} and found "
            f"{total_rows} result {row_label} relevant to the {plan.question_type} question."
        ),
        key_findings=key_findings,
        assumptions=plan.assumptions,
        limitations=[],
        confidence=min_confidence(plan.confidence, "high"),
    )


def parse_response_agent_response(raw_response: str) -> ResponseAgentResult:
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise ResponseAgentResponseError("Response Agent response is not valid JSON.") from error

    if not isinstance(payload, dict):
        raise ResponseAgentResponseError("Response Agent response must be a JSON object.")

    answer = require_string(payload, "answer").strip()
    if not answer:
        raise ResponseAgentResponseError("Response Agent response is missing answer.")

    return ResponseAgentResult(
        answer=answer,
        key_findings=require_string_list(payload, "key_findings"),
        assumptions=require_string_list(payload, "assumptions"),
        limitations=require_string_list(payload, "limitations"),
        confidence=require_confidence(payload),
    )


def require_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)

    if not isinstance(value, str):
        raise ResponseAgentResponseError(
            f"Response Agent response field '{field_name}' must be a string."
        )

    return value


def require_string_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name)

    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ResponseAgentResponseError(
            f"Response Agent response field '{field_name}' must be a list of strings."
        )

    return value


def require_confidence(payload: dict[str, Any]) -> Confidence:
    value = payload.get("confidence")

    if value not in {"high", "medium", "low"}:
        raise ResponseAgentResponseError(
            "Response Agent response field 'confidence' must be high, medium, or low."
        )

    return value


def min_confidence(left: Confidence, right: Confidence) -> Confidence:
    confidence_order = {"low": 0, "medium": 1, "high": 2}
    return left if confidence_order[left] <= confidence_order[right] else right

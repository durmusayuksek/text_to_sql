import json
import hashlib
from dataclasses import dataclass
from numbers import Number
from pathlib import Path
from typing import Any, Literal

from app.agents import openai_client
from app.agents.analysis_planner import AnalysisPlannerResult
from app.agents.query_agent import QueryAgentResult, query_agent_result_to_dict
from app.catalog import RedactionStrategy, get_data_catalog
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


@dataclass(frozen=True)
class ColumnRedactionPolicy:
    sensitive: bool = False
    redaction_strategy: RedactionStrategy = "omit"


def generate_response(
    question: str,
    plan: AnalysisPlannerResult,
    query_agent_result: QueryAgentResult,
    query_results: list[QueryExecutionResult],
) -> ResponseAgentResult:
    settings = get_settings()

    if settings.agent_mode == "openai":
        raw_response = openai_client.create_chat_completion(
            build_openai_messages(
                question,
                plan,
                query_agent_result,
                query_results,
                settings.response_agent_max_sample_rows,
            )
        )
        return parse_response_agent_response(raw_response)

    return build_mock_response(plan, query_results)


def build_openai_messages(
    question: str,
    plan: AnalysisPlannerResult,
    query_agent_result: QueryAgentResult,
    query_results: list[QueryExecutionResult],
    max_sample_rows: int,
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
                    "query_result_summaries": summarize_query_results(
                        query_results,
                        max_sample_rows=max_sample_rows,
                    ),
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

    limitations = [
        warning
        for result in query_results
        for warning in result.warnings
    ]

    return ResponseAgentResult(
        answer=(
            f"I ran {len(query_results)} validated {query_label} and found "
            f"{total_rows} result {row_label} relevant to the {plan.question_type} question."
        ),
        key_findings=key_findings,
        assumptions=plan.assumptions,
        limitations=limitations,
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


def summarize_query_results(
    query_results: list[QueryExecutionResult],
    max_sample_rows: int,
) -> list[dict[str, Any]]:
    return [
        summarize_query_result(
            query_result,
            max_sample_rows=max_sample_rows,
        )
        for query_result in query_results
    ]


def summarize_query_result(
    query_result: QueryExecutionResult,
    max_sample_rows: int,
) -> dict[str, Any]:
    redaction_policies = get_column_redaction_policies()
    column_names = get_visible_column_names(query_result.rows, redaction_policies)
    sample_rows = build_redacted_sample_rows(
        query_result.rows[:max_sample_rows],
        redaction_policies,
    )

    return {
        "query_id": query_result.query_id,
        "purpose": query_result.purpose,
        "sql": query_result.sql,
        "row_count": len(query_result.rows),
        "columns": column_names,
        "redacted_columns": get_redacted_columns(
            query_result.rows,
            redaction_policies,
        ),
        "sample_rows": sample_rows,
        "numeric_summaries": build_numeric_summaries(
            query_result.rows,
            column_names,
            redaction_policies,
        ),
        "warnings": query_result.warnings,
    }


def get_visible_column_names(
    rows: list[dict[str, Any]],
    redaction_policies: dict[str, ColumnRedactionPolicy],
) -> list[str]:
    column_names: list[str] = []

    for row in rows:
        for column_name in row:
            policy = get_redaction_policy(column_name, redaction_policies)

            if policy.sensitive and policy.redaction_strategy == "omit":
                continue

            if column_name not in column_names:
                column_names.append(column_name)

    return column_names


def build_redacted_sample_rows(
    rows: list[dict[str, Any]],
    redaction_policies: dict[str, ColumnRedactionPolicy],
) -> list[dict[str, Any]]:
    return [
        {
            column_name: redact_value(
                value,
                get_redaction_policy(column_name, redaction_policies),
            )
            for column_name, value in row.items()
            if should_include_column(
                get_redaction_policy(column_name, redaction_policies)
            )
        }
        for row in rows
    ]


def get_redacted_columns(
    rows: list[dict[str, Any]],
    redaction_policies: dict[str, ColumnRedactionPolicy],
) -> list[dict[str, str]]:
    redacted_columns: list[dict[str, str]] = []

    for row in rows:
        for column_name in row:
            policy = get_redaction_policy(column_name, redaction_policies)

            if not policy.sensitive:
                continue

            entry = {
                "name": column_name,
                "strategy": policy.redaction_strategy,
            }

            if entry not in redacted_columns:
                redacted_columns.append(entry)

    return redacted_columns


def should_include_column(policy: ColumnRedactionPolicy) -> bool:
    return not (policy.sensitive and policy.redaction_strategy == "omit")


def redact_value(value: Any, policy: ColumnRedactionPolicy) -> Any:
    if not policy.sensitive:
        return value

    if policy.redaction_strategy == "mask":
        return "***REDACTED***"

    if policy.redaction_strategy == "hash":
        return hash_value(value)

    return value


def hash_value(value: Any) -> str:
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_numeric_summaries(
    rows: list[dict[str, Any]],
    column_names: list[str],
    redaction_policies: dict[str, ColumnRedactionPolicy],
) -> dict[str, dict[str, float | int]]:
    summaries: dict[str, dict[str, float | int]] = {}

    for column_name in column_names:
        if get_redaction_policy(column_name, redaction_policies).sensitive:
            continue

        values = [
            value
            for row in rows
            for value in [row.get(column_name)]
            if is_numeric_summary_value(value)
        ]

        if not values:
            continue

        numeric_values = [float(value) for value in values]
        summaries[column_name] = {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
        }

    return summaries


def is_numeric_summary_value(value: Any) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)


def get_column_redaction_policies() -> dict[str, ColumnRedactionPolicy]:
    policies: dict[str, ColumnRedactionPolicy] = {}

    for table in get_data_catalog().tables:
        for column in table.columns:
            policies[column.name.lower()] = ColumnRedactionPolicy(
                sensitive=column.sensitive,
                redaction_strategy=column.redaction_strategy,
            )

    return policies


def get_redaction_policy(
    column_name: str,
    redaction_policies: dict[str, ColumnRedactionPolicy],
) -> ColumnRedactionPolicy:
    return redaction_policies.get(column_name.lower(), ColumnRedactionPolicy())

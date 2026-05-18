import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from app.agents import openai_client
from app.catalog import build_catalog_context
from app.config import get_settings

QuestionType = Literal[
    "summary",
    "comparison",
    "trend",
    "ranking",
    "lookup",
    "diagnostic",
    "unknown",
]
Confidence = Literal["high", "medium", "low"]
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "analysis_planner.md"


@dataclass(frozen=True)
class AnalysisPlannerResult:
    question_type: QuestionType
    required_tables: list[str]
    required_relationships: list[str]
    metrics: list[str]
    dimensions: list[str]
    filters: list[str]
    time_period: str | None
    requires_multiple_queries: bool
    analysis_steps: list[str]
    assumptions: list[str]
    confidence: Confidence
    catalog_context_used: str

    def to_prompt_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("catalog_context_used", None)
        return payload


class AnalysisPlannerError(RuntimeError):
    pass


class AnalysisPlannerResponseError(AnalysisPlannerError):
    pass


def plan_analysis(question: str) -> AnalysisPlannerResult:
    """Plan the analysis from catalog metadata only. This agent never generates SQL."""
    settings = get_settings()
    catalog_context = build_catalog_context()

    if settings.agent_mode == "openai":
        raw_response = openai_client.create_chat_completion(
            build_openai_messages(question, catalog_context)
        )
        return parse_analysis_planner_response(
            raw_response,
            catalog_context_used=catalog_context,
        )

    return build_mock_plan(question, catalog_context)


def build_openai_messages(question: str, catalog_context: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": load_analysis_planner_prompt(),
        },
        {
            "role": "user",
            "content": (
                f"User question:\n{question}\n\n"
                f"Data catalog metadata:\n{catalog_context}"
            ),
        },
    ]


def load_analysis_planner_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def parse_analysis_planner_response(
    raw_response: str,
    catalog_context_used: str = "",
) -> AnalysisPlannerResult:
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise AnalysisPlannerResponseError("Analysis Planner response is not valid JSON.") from error

    if not isinstance(payload, dict):
        raise AnalysisPlannerResponseError("Analysis Planner response must be a JSON object.")

    question_type = require_question_type(payload)
    confidence = require_confidence(payload, "Analysis Planner")

    return AnalysisPlannerResult(
        question_type=question_type,
        required_tables=require_string_list(payload, "required_tables"),
        required_relationships=require_string_list(payload, "required_relationships"),
        metrics=require_string_list(payload, "metrics"),
        dimensions=require_string_list(payload, "dimensions"),
        filters=require_string_list(payload, "filters"),
        time_period=require_optional_string(payload, "time_period"),
        requires_multiple_queries=require_bool(payload, "requires_multiple_queries"),
        analysis_steps=require_string_list(payload, "analysis_steps"),
        assumptions=require_string_list(payload, "assumptions"),
        confidence=confidence,
        catalog_context_used=catalog_context_used,
    )


def build_mock_plan(question: str, catalog_context: str) -> AnalysisPlannerResult:
    lowered_question = question.lower()

    if "passenger" in lowered_question or "pax" in lowered_question:
        return AnalysisPlannerResult(
            question_type="summary",
            required_tables=["sales_figures_since_2025"],
            required_relationships=[],
            metrics=["booked_pax"],
            dimensions=["route_direction"],
            filters=[],
            time_period="Use departure_date unless the question asks about booking date.",
            requires_multiple_queries=False,
            analysis_steps=["Aggregate booked passenger volume from sales records."],
            assumptions=["Passenger volume maps to booked_pax in sales_figures_since_2025."],
            confidence="high",
            catalog_context_used=catalog_context,
        )

    if "revenue" in lowered_question or "sales" in lowered_question:
        return AnalysisPlannerResult(
            question_type="summary",
            required_tables=["sales_figures_since_2025"],
            required_relationships=[],
            metrics=["net_revenue"],
            dimensions=["market_area"],
            filters=[],
            time_period=None,
            requires_multiple_queries=False,
            analysis_steps=["Aggregate net revenue from sales records."],
            assumptions=[],
            confidence="high",
            catalog_context_used=catalog_context,
        )

    return AnalysisPlannerResult(
        question_type="lookup",
        required_tables=["sales_figures_since_2025"],
        required_relationships=[],
        metrics=["booked_pax", "net_revenue"],
        dimensions=["booking_date", "departure_date", "route_direction", "market_area"],
        filters=[],
        time_period=None,
        requires_multiple_queries=False,
        analysis_steps=["Return relevant rows from the sales figures table."],
        assumptions=["The sales figures table is the only available catalog source."],
        confidence="medium",
        catalog_context_used=catalog_context,
    )


def require_question_type(payload: dict[str, Any]) -> QuestionType:
    value = payload.get("question_type")
    allowed = {"summary", "comparison", "trend", "ranking", "lookup", "diagnostic", "unknown"}

    if value not in allowed:
        raise AnalysisPlannerResponseError(
            "Analysis Planner response field 'question_type' is invalid."
        )

    return value


def require_confidence(payload: dict[str, Any], agent_name: str) -> Confidence:
    value = payload.get("confidence")

    if value not in {"high", "medium", "low"}:
        raise AnalysisPlannerResponseError(
            f"{agent_name} response field 'confidence' must be high, medium, or low."
        )

    return value


def require_string_list(payload: dict[str, Any], field_name: str) -> list[str]:
    value = payload.get(field_name)

    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if not isinstance(value, list):
        raise AnalysisPlannerResponseError(
            f"Analysis Planner response field '{field_name}' must be a list of strings."
        )

    normalized_values: list[str] = []

    for item in value:
        if item is None:
            continue

        if isinstance(item, str):
            normalized_values.append(item)
            continue

        normalized_values.append(json.dumps(item, sort_keys=True, default=str))

    return normalized_values


def require_optional_string(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)

    if value is None or isinstance(value, str):
        return value

    return json.dumps(value, sort_keys=True, default=str)


def require_bool(payload: dict[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)

    if isinstance(value, bool):
        return value

    raise AnalysisPlannerResponseError(
        f"Analysis Planner response field '{field_name}' must be a boolean."
    )

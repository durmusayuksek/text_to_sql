import re
from typing import Any

from app.agents.query_agent import generate_sql
from app.config import refresh_settings
from app.duckdb_layer.query_runner import run_query
from app.schemas.api import AskRequest, AskResponse

DESTRUCTIVE_INTENT_PATTERN = re.compile(
    r"\b(delete|update|drop|alter|insert|overwrite|remove|erase|truncate)\b",
    re.IGNORECASE,
)


class DestructiveIntentError(ValueError):
    pass


def answer_question(request: AskRequest) -> AskResponse:
    question = request.question.strip()
    validate_question(question)
    validate_safe_question_intent(question)

    settings = refresh_settings()
    query_agent_result = generate_sql(question)
    sql = query_agent_result.sql.strip().rstrip(";")
    rows = run_query(sql)

    return AskResponse(
        answer=build_answer(rows),
        sql=sql,
        explanation=query_agent_result.explanation,
        data=rows,
        query_agent_mode=settings.query_agent_mode,
    )


def validate_question(question: str) -> None:
    if not question.strip():
        raise ValueError("Question cannot be empty.")


def validate_safe_question_intent(question: str) -> None:
    match = DESTRUCTIVE_INTENT_PATTERN.search(question)

    if match:
        raise DestructiveIntentError(
            f"Destructive or modifying requests are not allowed: '{match.group(1)}'. "
            "This app only supports safe read-only analytical questions."
        )


def build_answer(rows: list[dict[str, Any]]) -> str:
    row_count = len(rows)
    row_label = "row" if row_count == 1 else "rows"
    return f"The query returned {row_count} {row_label}. Review the result table below."

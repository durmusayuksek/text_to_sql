import re

from app.agents.analysis_planner import plan_analysis
from app.agents.query_agent import generate_sql
from app.agents.response_agent import generate_response
from app.config import refresh_settings
from app.duckdb_layer.query_runner import QueryExecutionRequest, run_queries
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
    plan = plan_analysis(question)
    query_agent_result = generate_sql(question, plan)
    query_results = run_queries(
        [
            QueryExecutionRequest(
                query_id=query.query_id,
                purpose=query.purpose,
                sql=query.sql,
            )
            for query in query_agent_result.queries
        ]
    )
    response_agent_result = generate_response(
        question=question,
        plan=plan,
        query_agent_result=query_agent_result,
        query_results=query_results,
    )

    return AskResponse(
        answer=response_agent_result.answer,
        key_findings=response_agent_result.key_findings,
        assumptions=merge_unique(
            response_agent_result.assumptions,
            query_agent_result.assumptions,
        ),
        limitations=response_agent_result.limitations,
        confidence=response_agent_result.confidence,
        generated_sql_queries=[
            {
                "query_id": query.query_id,
                "purpose": query.purpose,
                "sql": query.sql,
            }
            for query in query_results
        ],
        query_results=(
            [query_result.to_response_payload() for query_result in query_results]
            if settings.debug_query_results
            else None
        ),
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

def merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []

    for group in groups:
        for item in group:
            if item not in merged:
                merged.append(item)

    return merged

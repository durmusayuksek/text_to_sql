import re
import time
import uuid
from dataclasses import asdict

from app.agents.analysis_planner import plan_analysis
from app.agents.query_agent import generate_sql, query_agent_result_to_dict
from app.agents.response_agent import generate_response
from app.ask_event_logger import (
    build_query_result_summaries,
    utc_now_iso,
    write_ask_event,
)
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
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()
    question = request.question.strip()
    settings = None
    event = build_initial_event(request_id, question)

    try:
        settings = refresh_settings()
        event["agent_mode"] = settings.agent_mode

        validate_question(question)
        validate_safe_question_intent(question)

        plan = plan_analysis(question)
        event["planner_output"] = plan.to_prompt_payload()

        query_agent_result = generate_sql(question, plan)
        event["query_agent_output"] = query_agent_result_to_dict(query_agent_result)

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
        event["validated_queries"] = [
            {
                "query_id": query.query_id,
                "purpose": query.purpose,
                "sql": query.sql,
            }
            for query in query_results
        ]
        event["query_result_summaries"] = build_query_result_summaries(
            query_results,
            include_rows=settings.log_query_result_rows,
        )
        event["warnings"] = [
            warning
            for query_result in query_results
            for warning in query_result.warnings
        ]

        response_agent_result = generate_response(
            question=question,
            plan=plan,
            query_agent_result=query_agent_result,
            query_results=query_results,
        )
        event["response_agent_output"] = asdict(response_agent_result)

        assumptions = merge_unique(
            response_agent_result.assumptions,
            query_agent_result.assumptions,
        )
        event["final_answer"] = response_agent_result.answer
        event["key_findings"] = response_agent_result.key_findings
        event["assumptions"] = assumptions
        event["limitations"] = response_agent_result.limitations
        event["success"] = True

        return AskResponse(
            answer=response_agent_result.answer,
            key_findings=response_agent_result.key_findings,
            assumptions=assumptions,
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
            query_agent_mode=settings.agent_mode,
        )
    except Exception as error:
        event["errors"].append(
            {
                "type": error.__class__.__name__,
                "message": str(error),
            }
        )
        raise
    finally:
        event["latency_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
        if settings is not None:
            write_ask_event(event, settings)


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


def build_initial_event(request_id: str, question: str) -> dict:
    return {
        "request_id": request_id,
        "timestamp_utc": utc_now_iso(),
        "user_question": question,
        "agent_mode": None,
        "planner_output": None,
        "query_agent_output": None,
        "validated_queries": [],
        "query_result_summaries": [],
        "response_agent_output": None,
        "final_answer": None,
        "key_findings": [],
        "assumptions": [],
        "limitations": [],
        "warnings": [],
        "errors": [],
        "latency_ms": None,
        "success": False,
    }

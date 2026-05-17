from fastapi.testclient import TestClient
import pytest

from app.agents.analysis_planner import (
    AnalysisPlannerResponseError,
    plan_analysis,
    parse_analysis_planner_response,
)
from app.agents.query_agent import (
    QueryAgentLowConfidenceError,
    QueryAgentResponseError,
    build_openai_messages,
    generate_sql,
    parse_query_agent_response,
)
from app.agents.response_agent import (
    ResponseAgentResponseError,
    generate_response,
    parse_response_agent_response,
)
from app.ask_service import DestructiveIntentError, validate_safe_question_intent
from app.config import ConfigurationError, get_settings
from app.duckdb_layer.query_runner import (
    QueryExecutionRequest,
    QueryExecutionResult,
    run_queries,
)
from app.main import app


@pytest.fixture(autouse=True)
def default_query_agent_mode(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("QUERY_AGENT_MODE", "mock")
    monkeypatch.delenv("DEBUG_QUERY_RESULTS", raising=False)
    yield
    get_settings.cache_clear()


def test_planner_returns_valid_json_shape() -> None:
    result = parse_analysis_planner_response(
        """
        {
          "question_type": "summary",
          "required_tables": ["pax_forecast"],
          "required_relationships": [],
          "metrics": ["forecast_pax"],
          "dimensions": ["route"],
          "filters": [],
          "time_period": null,
          "requires_multiple_queries": false,
          "analysis_steps": ["Aggregate passenger volume."],
          "assumptions": [],
          "confidence": "high"
        }
        """,
        catalog_context_used="catalog",
    )

    assert result.question_type == "summary"
    assert result.required_tables == ["pax_forecast"]
    assert result.requires_multiple_queries is False
    assert result.catalog_context_used == "catalog"


def test_planner_normalizes_structured_filter_items() -> None:
    result = parse_analysis_planner_response(
        """
        {
          "question_type": "summary",
          "required_tables": ["pax_forecast"],
          "required_relationships": [
            {"left": "pax_forecast.route", "right": "pax_route_targets.route"}
          ],
          "metrics": ["forecast_pax"],
          "dimensions": ["route"],
          "filters": [
            {"column": "departure_date", "operator": "last_month"}
          ],
          "time_period": {"grain": "month", "offset": -1},
          "requires_multiple_queries": false,
          "analysis_steps": ["Aggregate passenger volume."],
          "assumptions": [],
          "confidence": "high"
        }
        """,
        catalog_context_used="catalog",
    )

    assert result.filters == ['{"column": "departure_date", "operator": "last_month"}']
    assert result.required_relationships == [
        '{"left": "pax_forecast.route", "right": "pax_route_targets.route"}'
    ]
    assert result.time_period == '{"grain": "month", "offset": -1}'


def test_mock_planner_uses_catalog_metadata() -> None:
    result = plan_analysis("Show passenger volume by route")

    assert result.required_tables == ["pax_forecast"]
    assert "forecast_pax" in result.metrics
    assert "pax_forecast" in result.catalog_context_used
    assert "read_parquet" not in result.catalog_context_used


def test_query_agent_returns_queries_array() -> None:
    plan = plan_analysis("Show passenger volume by route")
    result = generate_sql("Show passenger volume by route", plan)

    assert len(result.queries) == 1
    assert result.queries[0].query_id == "main"
    assert "FROM pax_forecast" in result.queries[0].sql
    assert result.confidence == "high"


def test_valid_query_agent_json_response_parses_queries() -> None:
    result = parse_query_agent_response(
        """
        {
          "queries": [
            {
              "query_id": "main",
              "purpose": "Returns sample QA rows.",
              "sql": "SELECT * FROM qa LIMIT 10"
            }
          ],
          "assumptions": ["The user wants a sample."],
          "confidence": "high"
        }
        """,
        schema_context_used="schema context",
    )

    assert result.queries[0].sql == "SELECT * FROM qa LIMIT 10"
    assert result.queries[0].purpose == "Returns sample QA rows."
    assert result.confidence == "high"
    assert result.assumptions == ["The user wants a sample."]
    assert result.schema_context_used == "schema context"


def test_malformed_query_agent_json_response_fails() -> None:
    with pytest.raises(QueryAgentResponseError, match="not valid JSON"):
        parse_query_agent_response("{bad json")


def test_query_agent_response_missing_queries_fails() -> None:
    with pytest.raises(QueryAgentResponseError, match="queries"):
        parse_query_agent_response(
            """
            {
              "confidence": "low",
              "assumptions": []
            }
            """
        )


def test_multiple_duckdb_query_results_are_collected() -> None:
    results = run_queries(
        [
            QueryExecutionRequest(
                query_id="metrics",
                purpose="Return QA metrics.",
                sql="SELECT * FROM qa LIMIT 1",
            ),
            QueryExecutionRequest(
                query_id="passengers",
                purpose="Return passenger volume by route.",
                sql=(
                    "SELECT route, SUM(forecast_pax) AS forecast_passengers "
                    "FROM pax_forecast GROUP BY route LIMIT 2"
                ),
            ),
        ]
    )

    assert [result.query_id for result in results] == ["metrics", "passengers"]
    assert all(result.rows for result in results)


def test_invalid_sql_is_blocked_in_multi_query_execution() -> None:
    with pytest.raises(Exception, match="DROP statements are not allowed"):
        run_queries(
            [
                QueryExecutionRequest(
                    query_id="safe",
                    purpose="Return QA rows.",
                    sql="SELECT * FROM qa LIMIT 1",
                ),
                QueryExecutionRequest(
                    query_id="unsafe",
                    purpose="Attempt unsafe SQL.",
                    sql="DROP TABLE qa",
                ),
            ]
        )


def test_response_agent_returns_business_friendly_answer() -> None:
    plan = plan_analysis("Show passenger volume by route")
    query_agent_result = generate_sql("Show passenger volume by route", plan)
    response = generate_response(
        question="Show passenger volume by route",
        plan=plan,
        query_agent_result=query_agent_result,
        query_results=[
            QueryExecutionResult(
                query_id="main",
                purpose="Aggregate passenger volume by route.",
                sql="SELECT route, SUM(forecast_pax) AS forecast_passengers FROM pax_forecast GROUP BY route",
                rows=[{"route": "Stockholm-Tallinn", "forecast_passengers": 1840}],
            )
        ],
    )

    assert "validated query" in response.answer
    assert response.key_findings
    assert response.confidence in {"high", "medium", "low"}


def test_response_agent_json_response_parses() -> None:
    result = parse_response_agent_response(
        """
        {
          "answer": "Passenger volume is highest on Stockholm-Tallinn.",
          "key_findings": ["Stockholm-Tallinn leads."],
          "assumptions": [],
          "limitations": [],
          "confidence": "high"
        }
        """
    )

    assert result.answer.startswith("Passenger volume")
    assert result.key_findings == ["Stockholm-Tallinn leads."]


def test_response_agent_json_response_rejects_missing_answer() -> None:
    with pytest.raises(ResponseAgentResponseError, match="answer"):
        parse_response_agent_response(
            """
            {
              "answer": "",
              "key_findings": [],
              "assumptions": [],
              "limitations": [],
              "confidence": "low"
            }
            """
        )


def test_api_ask_accepts_question_without_module_id(monkeypatch) -> None:
    from app.config import Settings

    monkeypatch.setattr(
        "app.ask_service.refresh_settings",
        lambda: Settings(query_agent_mode="mock"),
    )

    client = TestClient(app)
    response = client.post("/api/ask", json={"question": "Show one row"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert payload["generated_sql_queries"][0]["query_id"] == "main"
    assert payload["query_results"] is None
    assert payload["query_agent_mode"] == "mock"
    assert "module_id" not in payload


def test_api_ask_includes_query_results_when_debug_enabled(monkeypatch) -> None:
    from app.config import Settings

    monkeypatch.setattr(
        "app.ask_service.refresh_settings",
        lambda: Settings(query_agent_mode="mock", debug_query_results=True),
    )

    client = TestClient(app)
    response = client.post("/api/ask", json={"question": "Show one row"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["query_results"][0]["rows"]


def test_destructive_intent_guard_blocks_question() -> None:
    with pytest.raises(DestructiveIntentError, match="delete"):
        validate_safe_question_intent("Please delete old QA rows")


def test_api_ask_blocks_destructive_intent_before_query_agent(monkeypatch) -> None:
    def fail_if_called(question: str):
        raise AssertionError("Planner should not be called for destructive intent.")

    monkeypatch.setattr("app.ask_service.plan_analysis", fail_if_called)

    client = TestClient(app)
    response = client.post("/api/ask", json={"question": "Drop the qa table"})

    assert response.status_code == 400
    assert "Destructive or modifying requests are not allowed" in response.json()["detail"]


def test_openai_mode_uses_mocked_openai_responses(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("QUERY_AGENT_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")

    responses = iter(
        [
            """
            {
              "question_type": "lookup",
              "required_tables": ["qa"],
              "required_relationships": [],
              "metrics": ["value"],
              "dimensions": ["topic", "metric"],
              "filters": [],
              "time_period": null,
              "requires_multiple_queries": false,
              "analysis_steps": ["Return QA rows."],
              "assumptions": [],
              "confidence": "high"
            }
            """,
            """
            {
              "queries": [
                {
                  "query_id": "main",
                  "purpose": "Returns QA rows.",
                  "sql": "SELECT * FROM qa LIMIT 10"
                }
              ],
              "assumptions": [],
              "confidence": "high"
            }
            """,
        ]
    )

    captured_messages: list[list[dict[str, str]]] = []

    def fake_create_chat_completion(messages: list[dict[str, str]]) -> str:
        captured_messages.append(messages)
        return next(responses)

    monkeypatch.setattr(
        "app.agents.analysis_planner.openai_client.create_chat_completion",
        fake_create_chat_completion,
    )
    monkeypatch.setattr(
        "app.agents.query_agent.openai_client.create_chat_completion",
        fake_create_chat_completion,
    )

    plan = plan_analysis("Show QA rows")
    result = generate_sql("Show QA rows", plan)

    assert result.queries[0].sql == "SELECT * FROM qa LIMIT 10"
    assert "read_parquet" not in captured_messages[1][1]["content"]
    assert "Analysis Planner output" in captured_messages[1][1]["content"]

    get_settings.cache_clear()


def test_openai_mode_missing_api_key_fails(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("QUERY_AGENT_MODE", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY is required"):
        plan_analysis("Show QA rows")

    get_settings.cache_clear()


def test_openai_low_confidence_query_response_fails(monkeypatch) -> None:
    plan = plan_analysis("Show QA rows")

    get_settings.cache_clear()
    monkeypatch.setenv("QUERY_AGENT_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    def fake_create_chat_completion(messages: list[dict[str, str]]) -> str:
        return """
        {
          "queries": [
            {
              "query_id": "main",
              "purpose": "Low confidence query.",
              "sql": "SELECT * FROM qa LIMIT 10"
            }
          ],
          "assumptions": ["Insufficient metadata."],
          "confidence": "low"
        }
        """

    monkeypatch.setattr(
        "app.agents.query_agent.openai_client.create_chat_completion",
        fake_create_chat_completion,
    )

    with pytest.raises(QueryAgentLowConfidenceError, match="low confidence"):
        generate_sql("Show QA rows", plan)

    get_settings.cache_clear()


def test_openai_messages_include_only_metadata_and_plan_context() -> None:
    plan = plan_analysis("Show QA rows")
    messages = build_openai_messages(
        question="Show QA rows",
        plan=plan,
        schema_context="Catalog metadata only",
    )

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "Show QA rows" in messages[1]["content"]
    assert "Catalog metadata only" in messages[1]["content"]
    assert "Analysis Planner output" in messages[1]["content"]
    assert "read_parquet(" not in messages[1]["content"]


def test_malformed_planner_json_response_fails() -> None:
    with pytest.raises(AnalysisPlannerResponseError, match="not valid JSON"):
        parse_analysis_planner_response("{bad json")

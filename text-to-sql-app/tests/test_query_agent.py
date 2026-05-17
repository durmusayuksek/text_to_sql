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
    build_openai_messages as build_response_openai_messages,
    generate_response,
    parse_response_agent_response,
)
from app.ask_service import DestructiveIntentError, validate_safe_question_intent
from app.catalog import ColumnDefinition, DataCatalog, TableDefinition
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
    monkeypatch.setenv("AGENT_MODE", "mock")
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


def test_response_agent_openai_payload_uses_minimized_query_results() -> None:
    plan = plan_analysis("Show QA rows")
    query_agent_result = generate_sql("Show QA rows", plan)
    query_results = [
        QueryExecutionResult(
            query_id="main",
            purpose="Return QA rows.",
            sql="SELECT * FROM qa LIMIT 10",
            rows=[
                {"metric": f"metric_{index}", "value": index}
                for index in range(10)
            ],
        )
    ]

    messages = build_response_openai_messages(
        question="Show QA rows",
        plan=plan,
        query_agent_result=query_agent_result,
        query_results=query_results,
        max_sample_rows=2,
    )
    payload = __import__("json").loads(messages[1]["content"])
    summary = payload["query_result_summaries"][0]

    assert "query_results" not in payload
    assert summary["row_count"] == 10
    assert summary["columns"] == ["metric", "value"]
    assert len(summary["sample_rows"]) == 2
    assert summary["sample_rows"][0]["metric"] == "metric_0"
    assert "metric_9" not in messages[1]["content"]
    assert summary["numeric_summaries"]["value"]["max"] == 9.0


def test_response_agent_max_sample_rows_setting_is_respected(monkeypatch) -> None:
    from app.config import Settings

    plan = plan_analysis("Show QA rows")
    query_agent_result = generate_sql("Show QA rows", plan)
    query_results = [
        QueryExecutionResult(
            query_id="main",
            purpose="Return QA rows.",
            sql="SELECT * FROM qa LIMIT 10",
            rows=[
                {"metric": f"metric_{index}", "value": index}
                for index in range(4)
            ],
        )
    ]
    captured_messages: list[dict[str, str]] = []

    monkeypatch.setattr(
        "app.agents.response_agent.get_settings",
        lambda: Settings(
            agent_mode="openai",
            openai_api_key="test-key",
            response_agent_max_sample_rows=1,
        ),
    )

    def fake_create_chat_completion(messages: list[dict[str, str]]) -> str:
        captured_messages.extend(messages)
        return """
        {
          "answer": "One row sample was used.",
          "key_findings": [],
          "assumptions": [],
          "limitations": [],
          "confidence": "high"
        }
        """

    monkeypatch.setattr(
        "app.agents.response_agent.openai_client.create_chat_completion",
        fake_create_chat_completion,
    )

    generate_response(
        question="Show QA rows",
        plan=plan,
        query_agent_result=query_agent_result,
        query_results=query_results,
    )

    payload = __import__("json").loads(captured_messages[1]["content"])
    assert len(payload["query_result_summaries"][0]["sample_rows"]) == 1


def test_sensitive_column_with_omit_is_not_sent_to_openai(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.agents.response_agent.get_data_catalog",
        lambda: DataCatalog(
            description="test catalog",
            tables=(
                TableDefinition(
                    table_name="customers",
                    data_path="data/customers.parquet",
                    description="Customer records.",
                    columns=(
                        ColumnDefinition(
                            name="customer_email",
                            type="VARCHAR",
                            description="Customer email.",
                            sensitive=True,
                            redaction_strategy="omit",
                        ),
                        ColumnDefinition(
                            name="revenue",
                            type="DOUBLE",
                            description="Revenue.",
                        ),
                    ),
                ),
            ),
            relationships=(),
            example_questions=(),
            example_sql=(),
        ),
    )

    payload = build_response_payload_for_rows(
        [
            {
                "customer_email": "person@example.com",
                "revenue": 100.0,
            }
        ]
    )
    summary = payload["query_result_summaries"][0]

    assert "customer_email" not in summary["columns"]
    assert "customer_email" not in summary["sample_rows"][0]
    assert "customer_email" not in summary["numeric_summaries"]
    assert summary["redacted_columns"] == [
        {"name": "customer_email", "strategy": "omit"}
    ]
    assert "person@example.com" not in __import__("json").dumps(payload)
    assert summary["sample_rows"][0]["revenue"] == 100.0


def test_sensitive_column_with_mask_is_redacted_in_openai_payload(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.agents.response_agent.get_data_catalog",
        lambda: DataCatalog(
            description="test catalog",
            tables=(
                TableDefinition(
                    table_name="customers",
                    data_path="data/customers.parquet",
                    description="Customer records.",
                    columns=(
                        ColumnDefinition(
                            name="customer_email",
                            type="VARCHAR",
                            description="Customer email.",
                            sensitive=True,
                            redaction_strategy="mask",
                        ),
                        ColumnDefinition(
                            name="customer_count",
                            type="INTEGER",
                            description="Customer count.",
                            sensitive=True,
                            redaction_strategy="mask",
                        ),
                        ColumnDefinition(
                            name="route",
                            type="VARCHAR",
                            description="Route.",
                        ),
                    ),
                ),
            ),
            relationships=(),
            example_questions=(),
            example_sql=(),
        ),
    )

    payload = build_response_payload_for_rows(
        [
            {
                "customer_email": "person@example.com",
                "customer_count": 42,
                "route": "Stockholm-Tallinn",
            }
        ]
    )
    summary = payload["query_result_summaries"][0]

    assert "customer_email" in summary["columns"]
    assert summary["sample_rows"][0]["customer_email"] == "***REDACTED***"
    assert summary["sample_rows"][0]["customer_count"] == "***REDACTED***"
    assert "customer_count" not in summary["numeric_summaries"]
    assert summary["sample_rows"][0]["route"] == "Stockholm-Tallinn"
    assert "person@example.com" not in __import__("json").dumps(payload)


def test_default_non_sensitive_columns_are_included_in_openai_payload() -> None:
    payload = build_response_payload_for_rows(
        [
            {
                "metric": "on_time_departure_rate",
                "value": 0.91,
            }
        ]
    )
    summary = payload["query_result_summaries"][0]

    assert summary["columns"] == ["metric", "value"]
    assert summary["sample_rows"][0]["metric"] == "on_time_departure_rate"
    assert summary["numeric_summaries"]["value"]["max"] == 0.91


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


def test_empty_query_results_do_not_fail_multi_query_execution() -> None:
    results = run_queries(
        [
            QueryExecutionRequest(
                query_id="empty",
                purpose="Return no QA rows.",
                sql="SELECT * FROM qa WHERE 1 = 0",
            ),
            QueryExecutionRequest(
                query_id="non_empty",
                purpose="Return one QA row.",
                sql="SELECT * FROM qa LIMIT 1",
            ),
        ]
    )

    assert results[0].rows == []
    assert results[0].warnings == ["Query 'empty' returned no rows."]
    assert results[1].rows


def test_empty_query_result_creates_response_limitation() -> None:
    plan = plan_analysis("Show QA rows")
    query_agent_result = generate_sql("Show QA rows", plan)
    response = generate_response(
        question="Show QA rows",
        plan=plan,
        query_agent_result=query_agent_result,
        query_results=[
            QueryExecutionResult(
                query_id="empty",
                purpose="Return no QA rows.",
                sql="SELECT * FROM qa WHERE 1 = 0",
                rows=[],
                warnings=["Query 'empty' returned no rows."],
            )
        ],
    )

    assert response.limitations == ["Query 'empty' returned no rows."]


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
    monkeypatch.setenv("AGENT_MODE", "openai")
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
    monkeypatch.setenv("AGENT_MODE", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY is required"):
        plan_analysis("Show QA rows")

    get_settings.cache_clear()


def test_openai_low_confidence_query_response_fails(monkeypatch) -> None:
    plan = plan_analysis("Show QA rows")

    get_settings.cache_clear()
    monkeypatch.setenv("AGENT_MODE", "openai")
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


def test_agent_mode_setting_takes_precedence(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("AGENT_MODE", "mock")
    monkeypatch.setenv("QUERY_AGENT_MODE", "openai")

    settings = get_settings()

    assert settings.agent_mode == "mock"
    assert settings.query_agent_mode == "mock"

    get_settings.cache_clear()


def test_query_agent_mode_fallback_still_works(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.delenv("AGENT_MODE", raising=False)
    monkeypatch.setenv("QUERY_AGENT_MODE", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = get_settings()

    assert settings.agent_mode == "openai"
    assert settings.query_agent_mode == "openai"

    get_settings.cache_clear()


def build_response_payload_for_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    plan = plan_analysis("Show rows")
    query_agent_result = generate_sql("Show rows", plan)
    messages = build_response_openai_messages(
        question="Show rows",
        plan=plan,
        query_agent_result=query_agent_result,
        query_results=[
            QueryExecutionResult(
                query_id="main",
                purpose="Return rows.",
                sql="SELECT * FROM test_table LIMIT 10",
                rows=rows,
            )
        ],
        max_sample_rows=5,
    )

    return __import__("json").loads(messages[1]["content"])

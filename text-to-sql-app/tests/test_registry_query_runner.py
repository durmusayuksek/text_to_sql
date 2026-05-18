from app.catalog import build_catalog_context
from app.duckdb_layer.query_runner import (
    InvalidQueryError,
    QueryExecutionRequest,
    run_queries,
    run_query,
)


def test_catalog_query_can_use_registered_sales_table() -> None:
    rows = run_query(
        """
        SELECT route_direction, SUM(booked_pax) AS booked_passengers
        FROM sales_figures_since_2025
        GROUP BY route_direction
        LIMIT 10
        """,
    )

    assert rows
    assert {"route_direction", "booked_passengers"} <= set(rows[0])


def test_query_runner_blocks_tables_outside_catalog() -> None:
    try:
        run_query("SELECT * FROM unknown_table LIMIT 10")
    except InvalidQueryError as error:
        assert "Table 'unknown_table' is not allowed" in str(error)
    else:
        raise AssertionError("Expected InvalidQueryError")


def test_run_queries_validates_each_query() -> None:
    try:
        run_queries(
            [
                QueryExecutionRequest(
                    query_id="safe",
                    purpose="Return sales rows.",
                    sql="SELECT * FROM sales_figures_since_2025 LIMIT 1",
                ),
                QueryExecutionRequest(
                    query_id="unsafe",
                    purpose="Attempt to read files.",
                    sql="SELECT * FROM read_parquet('data/sales/sales_figures_since_2025.parquet')",
                ),
            ]
        )
    except InvalidQueryError as error:
        assert "read_parquet" in str(error)
    else:
        raise AssertionError("Expected InvalidQueryError")


def test_agent_schema_context_uses_catalog_metadata() -> None:
    context = build_catalog_context()

    assert "Data catalog for Question & Answer Text-to-SQL" in context
    assert "sales_figures_since_2025" in context
    assert "Relationships:" in context
    assert "- None defined." in context
    assert "Example SQL:" in context
    assert "read_parquet" not in context

from app.duckdb_layer.query_runner import InvalidQueryError, run_query
from app.modules.registry import build_agent_schema_context


def test_module_join_query_can_use_multiple_registered_tables() -> None:
    rows = run_query(
        "pax_forecast",
        """
        SELECT pf.route, pf.forecast_pax, rt.target_load_factor
        FROM pax_forecast pf
        JOIN pax_route_targets rt ON pf.route = rt.route
        LIMIT 10
        """,
    )

    assert rows
    assert {"route", "forecast_pax", "target_load_factor"} <= set(rows[0])


def test_query_runner_blocks_tables_outside_selected_module() -> None:
    try:
        run_query("qa", "SELECT * FROM pax_forecast LIMIT 10")
    except InvalidQueryError as error:
        assert "Table 'pax_forecast' is not allowed" in str(error)
    else:
        raise AssertionError("Expected InvalidQueryError")


def test_agent_schema_context_uses_registry_metadata() -> None:
    context = build_agent_schema_context("pax_forecast")

    assert "Module: Pax Forecast" in context
    assert "pax_forecast" in context
    assert "pax_route_targets" in context
    assert "Relationships:" in context
    assert "Example SQL:" in context
    assert "read_parquet" not in context

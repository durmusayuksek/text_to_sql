from dataclasses import dataclass

from app.modules.registry import build_agent_schema_context, get_module_config


@dataclass(frozen=True)
class QueryAgentResult:
    sql: str
    explanation: str
    schema_context_used: str


def generate_sql(module_id: str, question: str) -> QueryAgentResult:
    """Generate deterministic mocked SQL from registry metadata only."""
    schema_context = build_agent_schema_context(module_id)
    module = get_module_config(module_id)

    return QueryAgentResult(
        sql=get_mock_sql(module.module_id),
        explanation=get_mock_explanation(module.module_id),
        schema_context_used=schema_context,
    )


def get_mock_sql(module_id: str) -> str:
    mocked_sql_by_module = {
        "pax_forecast": (
            "SELECT pf.departure_date, pf.route, pf.forecast_pax, pf.capacity, "
            "pf.load_factor, rt.target_load_factor, rt.priority "
            "FROM pax_forecast pf "
            "JOIN pax_route_targets rt ON pf.route = rt.route "
            "LIMIT 10"
        ),
        "special_cruise_profit": "SELECT * FROM special_cruise_profit LIMIT 10",
        "qa": "SELECT * FROM qa LIMIT 10",
    }

    try:
        return mocked_sql_by_module[module_id]
    except KeyError as error:
        raise ValueError(f"No mocked SQL is configured for module_id '{module_id}'.") from error


def get_mock_explanation(module_id: str) -> str:
    mocked_explanations_by_module = {
        "pax_forecast": "This mocked query joins forecast rows to route-level target metadata.",
        "special_cruise_profit": "This mocked query returns sample rows for entertainment profit analysis.",
        "qa": "This mocked query returns sample rows for general analysis.",
    }

    try:
        return mocked_explanations_by_module[module_id]
    except KeyError as error:
        raise ValueError(f"No mocked SQL explanation is configured for module_id '{module_id}'.") from error

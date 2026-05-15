from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

ModuleId = str


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    type: str
    description: str
    examples: tuple[str, ...] = ()
    business_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class TableDefinition:
    table_name: str
    data_path: str
    description: str
    columns: tuple[ColumnDefinition, ...]


@dataclass(frozen=True)
class RelationshipDefinition:
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    relationship_type: str
    description: str


@dataclass(frozen=True)
class ProcessorResult:
    answer: str
    sql: str
    explanation: str
    data: list[dict[str, Any]]


ProcessorFunction = Callable[
    [Mapping[str, Any], str, Mapping[str, Any]],
    ProcessorResult,
]


@dataclass(frozen=True)
class ModuleConfig:
    module_id: ModuleId
    label: str
    description: str
    tables: tuple[TableDefinition, ...]
    relationships: tuple[RelationshipDefinition, ...]
    processor_function: ProcessorFunction
    example_questions: tuple[str, ...]
    example_sql: tuple[str, ...]


# Processor imports live below shared registry types so processor files can use
# ProcessorResult without creating an import cycle.
from app.modules import pax_forecast, qa, special_cruise_profit


MODULE_REGISTRY: dict[ModuleId, ModuleConfig] = {
    "pax_forecast": ModuleConfig(
        module_id="pax_forecast",
        label="Pax Forecast",
        description="Ask forecasting questions about demand, occupancy, and passenger volume trends.",
        tables=(
            TableDefinition(
                table_name="pax_forecast",
                data_path="data/pax_forecast/pax_forecast.parquet",
                description="Passenger forecast rows by departure date and route.",
                columns=(
                    ColumnDefinition(
                        name="departure_date",
                        type="DATE",
                        description="Scheduled departure date.",
                        examples=("2026-06-01",),
                        business_terms=("sailing date", "departure"),
                    ),
                    ColumnDefinition(
                        name="route",
                        type="VARCHAR",
                        description="Commercial route for the sailing.",
                        examples=("Stockholm-Tallinn",),
                        business_terms=("line", "route"),
                    ),
                    ColumnDefinition(
                        name="forecast_pax",
                        type="INTEGER",
                        description="Forecasted passenger count.",
                        examples=("1840",),
                        business_terms=("pax", "passengers", "demand"),
                    ),
                    ColumnDefinition(
                        name="capacity",
                        type="INTEGER",
                        description="Available passenger capacity.",
                        examples=("2100",),
                        business_terms=("inventory", "capacity"),
                    ),
                    ColumnDefinition(
                        name="load_factor",
                        type="DECIMAL",
                        description="Forecasted passenger count divided by capacity.",
                        examples=("0.87",),
                        business_terms=("occupancy", "fill rate"),
                    ),
                ),
            ),
            TableDefinition(
                table_name="pax_route_targets",
                data_path="data/pax_forecast/pax_route_targets.parquet",
                description="Route-level target load factors for forecast comparison.",
                columns=(
                    ColumnDefinition(
                        name="route",
                        type="VARCHAR",
                        description="Commercial route matching pax_forecast.route.",
                        examples=("Stockholm-Tallinn",),
                        business_terms=("line", "route"),
                    ),
                    ColumnDefinition(
                        name="target_load_factor",
                        type="DECIMAL",
                        description="Target occupancy ratio for the route.",
                        examples=("0.85",),
                        business_terms=("target occupancy", "target fill rate"),
                    ),
                    ColumnDefinition(
                        name="priority",
                        type="VARCHAR",
                        description="Planning priority band for the route.",
                        examples=("high", "medium"),
                        business_terms=("planning priority",),
                    ),
                ),
            ),
        ),
        relationships=(
            RelationshipDefinition(
                left_table="pax_forecast",
                left_column="route",
                right_table="pax_route_targets",
                right_column="route",
                relationship_type="many_to_one",
                description="Each forecast row can join to one route target by route.",
            ),
        ),
        processor_function=pax_forecast.process,
        example_questions=(
            "Which sailings are forecast to exceed capacity targets next month?",
            "Show forecasted passenger volume by route.",
        ),
        example_sql=(
            "SELECT * FROM pax_forecast LIMIT 10",
            "SELECT pf.route, pf.forecast_pax, rt.target_load_factor FROM pax_forecast pf JOIN pax_route_targets rt ON pf.route = rt.route LIMIT 10",
        ),
    ),
    "special_cruise_profit": ModuleConfig(
        module_id="special_cruise_profit",
        label="Special Cruise / Entertainment Profit Calculation",
        description="Explore revenue, cost, margin, and profitability scenarios for special cruise events.",
        tables=(
            TableDefinition(
                table_name="special_cruise_profit",
                data_path="data/special_cruise/special_cruise_profit.parquet",
                description="Event-level revenue, cost, and margin records.",
                columns=(
                    ColumnDefinition(
                        name="event_id",
                        type="VARCHAR",
                        description="Unique special cruise event identifier.",
                        examples=("EVT-1001",),
                        business_terms=("event", "cruise event"),
                    ),
                    ColumnDefinition(
                        name="event_name",
                        type="VARCHAR",
                        description="Display name of the entertainment event.",
                        examples=("Jazz Night",),
                        business_terms=("show", "entertainment"),
                    ),
                    ColumnDefinition(
                        name="ticket_revenue",
                        type="INTEGER",
                        description="Ticket revenue attributed to the event.",
                        examples=("125000",),
                        business_terms=("revenue", "sales"),
                    ),
                    ColumnDefinition(
                        name="entertainment_cost",
                        type="INTEGER",
                        description="Direct entertainment cost for the event.",
                        examples=("85000",),
                        business_terms=("cost", "artist fee"),
                    ),
                    ColumnDefinition(
                        name="margin",
                        type="DECIMAL",
                        description="Contribution margin ratio for the event.",
                        examples=("0.32",),
                        business_terms=("profitability", "margin"),
                    ),
                ),
            ),
        ),
        relationships=(),
        processor_function=special_cruise_profit.process,
        example_questions=(
            "What attendance level is needed to break even?",
            "Which entertainment events have the strongest mocked margin?",
        ),
        example_sql=("SELECT * FROM special_cruise_profit LIMIT 10",),
    ),
    "qa": ModuleConfig(
        module_id="qa",
        label="Questions / Answers",
        description="Use a general analytical workspace for direct questions over prepared datasets.",
        tables=(
            TableDefinition(
                table_name="qa",
                data_path="data/qa/qa.parquet",
                description="General analytical metrics by topic.",
                columns=(
                    ColumnDefinition(
                        name="topic",
                        type="VARCHAR",
                        description="Business area for the metric.",
                        examples=("operations", "finance"),
                        business_terms=("domain", "area"),
                    ),
                    ColumnDefinition(
                        name="metric",
                        type="VARCHAR",
                        description="Metric identifier.",
                        examples=("on_time_departure_rate",),
                        business_terms=("KPI", "measure"),
                    ),
                    ColumnDefinition(
                        name="value",
                        type="DOUBLE",
                        description="Metric value.",
                        examples=("0.91", "285.5"),
                        business_terms=("value", "result"),
                    ),
                    ColumnDefinition(
                        name="updated_at",
                        type="DATE",
                        description="Date the metric was last refreshed.",
                        examples=("2026-05-01",),
                        business_terms=("refresh date", "as of date"),
                    ),
                ),
            ),
        ),
        relationships=(),
        processor_function=qa.process,
        example_questions=(
            "Summarize the most important operational signal.",
            "Rank the available sample metrics.",
        ),
        example_sql=("SELECT * FROM qa LIMIT 10",),
    ),
}


class UnknownModuleError(ValueError):
    pass


def get_registered_modules() -> list[ModuleConfig]:
    return list(MODULE_REGISTRY.values())


def get_module_config(module_id: str) -> ModuleConfig:
    try:
        return MODULE_REGISTRY[module_id]  # type: ignore[index]
    except KeyError as error:
        valid_values = ", ".join(sorted(MODULE_REGISTRY))
        raise UnknownModuleError(
            f"Unknown module_id '{module_id}'. Expected one of: {valid_values}."
        ) from error


def build_agent_schema_context(module_id: str) -> str:
    module = get_module_config(module_id)
    lines = [
        f"Module: {module.label} ({module.module_id})",
        f"Description: {module.description}",
        "",
        "Available tables:",
    ]

    for table in module.tables:
        lines.append(f"- {table.table_name}: {table.description}")
        for column in table.columns:
            extras = []
            if column.examples:
                extras.append(f"examples: {', '.join(column.examples)}")
            if column.business_terms:
                extras.append(f"business terms: {', '.join(column.business_terms)}")
            suffix = f" ({'; '.join(extras)})" if extras else ""
            lines.append(
                f"  - {column.name} [{column.type}]: {column.description}{suffix}"
            )

    lines.extend(["", "Relationships:"])
    if module.relationships:
        for relationship in module.relationships:
            lines.append(
                "- "
                f"{relationship.left_table}.{relationship.left_column} -> "
                f"{relationship.right_table}.{relationship.right_column} "
                f"({relationship.relationship_type}): {relationship.description}"
            )
    else:
        lines.append("- None defined.")

    lines.extend(["", "Example questions:"])
    lines.extend(f"- {question}" for question in module.example_questions)

    lines.extend(["", "Example SQL:"])
    lines.extend(f"- {sql}" for sql in module.example_sql)

    return "\n".join(lines)

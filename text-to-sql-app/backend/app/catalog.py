from dataclasses import dataclass
from typing import Literal


RedactionStrategy = Literal["omit", "mask", "hash"]


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    type: str
    description: str
    examples: tuple[str, ...] = ()
    business_terms: tuple[str, ...] = ()
    sensitive: bool = False
    redaction_strategy: RedactionStrategy = "omit"


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
class DataCatalog:
    description: str
    tables: tuple[TableDefinition, ...]
    relationships: tuple[RelationshipDefinition, ...]
    example_questions: tuple[str, ...]
    example_sql: tuple[str, ...]


DATA_CATALOG = DataCatalog(
    description=(
        "Central catalog for the single Question & Answer Text-to-SQL workflow. "
        "Tables are available analytical data sources, not selectable application modules."
    ),
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
                    business_terms=("pax", "passengers", "demand", "passenger volume"),
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
    example_questions=(
        "What was passenger volume last month?",
        "Show forecasted passenger volume by route.",
        "Rank the available sample metrics.",
        "Which entertainment events have the strongest margin?",
    ),
    example_sql=(
        "SELECT * FROM qa LIMIT 10",
        "SELECT route, SUM(forecast_pax) AS forecast_passengers FROM pax_forecast GROUP BY route ORDER BY forecast_passengers DESC LIMIT 10",
        "SELECT pf.route, pf.forecast_pax, rt.target_load_factor FROM pax_forecast pf JOIN pax_route_targets rt ON pf.route = rt.route LIMIT 10",
        "SELECT event_name, margin FROM special_cruise_profit ORDER BY margin DESC LIMIT 10",
    ),
)


def get_data_catalog() -> DataCatalog:
    return DATA_CATALOG


def get_allowed_table_names() -> list[str]:
    return [table.table_name for table in DATA_CATALOG.tables]


def build_catalog_context() -> str:
    catalog = get_data_catalog()
    lines = [
        "Data catalog for Question & Answer Text-to-SQL",
        f"Description: {catalog.description}",
        "",
        "Available tables:",
    ]

    for table in catalog.tables:
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
    if catalog.relationships:
        for relationship in catalog.relationships:
            lines.append(
                "- "
                f"{relationship.left_table}.{relationship.left_column} -> "
                f"{relationship.right_table}.{relationship.right_column} "
                f"({relationship.relationship_type}): {relationship.description}"
            )
    else:
        lines.append("- None defined.")

    lines.extend(["", "Example questions:"])
    lines.extend(f"- {question}" for question in catalog.example_questions)

    lines.extend(["", "Example SQL:"])
    lines.extend(f"- {sql}" for sql in catalog.example_sql)

    return "\n".join(lines)

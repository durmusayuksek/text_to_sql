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
            table_name="sales_figures_since_2025",
            data_path="data/sales/sales_figures_since_2025.parquet",
            description=(
                "Sales and passenger booking figures since 2025 by booking date, "
                "departure date, route, market, ship, and sales planning segment."
            ),
            columns=(
                ColumnDefinition(
                    name="booking_date",
                    type="DATE",
                    description="Date when the sale or booking was created.",
                    examples=("2025-06-18",),
                    business_terms=("booking date", "sale date", "created date"),
                ),
                ColumnDefinition(
                    name="departure_date",
                    type="DATE",
                    description="Scheduled departure date for the booked trip.",
                    examples=("2025-06-24",),
                    business_terms=("departure date", "sailing date", "travel date"),
                ),
                ColumnDefinition(
                    name="route_code",
                    type="VARCHAR",
                    description="Commercial route code for the trip.",
                    examples=("TUR-STO", "TAL-HEL"),
                    business_terms=("route", "line"),
                ),
                ColumnDefinition(
                    name="route_direction",
                    type="VARCHAR",
                    description="Directional route code for the sailing leg.",
                    examples=("TUR-STO", "HEL-TAL"),
                    business_terms=("direction", "route direction"),
                ),
                ColumnDefinition(
                    name="market_area",
                    type="VARCHAR",
                    description="Sales market area for the booking.",
                    examples=("SCANDINAVIA", "BALTIA", "FINLAND"),
                    business_terms=("market", "market area", "sales market"),
                ),
                ColumnDefinition(
                    name="ship_type",
                    type="VARCHAR",
                    description="Type or category of ship used for the trip.",
                    examples=("Shuttle",),
                    business_terms=("ship type", "vessel type"),
                ),
                ColumnDefinition(
                    name="ship_code",
                    type="VARCHAR",
                    description="Ship code or vessel name for the trip.",
                    examples=("MEGASTAR", "S.PRINCESS"),
                    business_terms=("ship", "vessel"),
                ),
                ColumnDefinition(
                    name="sales_planning_segment",
                    type="VARCHAR",
                    description="High-level sales planning segment.",
                    examples=("B2C",),
                    business_terms=("segment", "sales segment"),
                ),
                ColumnDefinition(
                    name="sales_planning_subsegment",
                    type="VARCHAR",
                    description="Detailed sales planning subsegment.",
                    examples=("B2C PUBLIC PRICE", "B2C CAMPAIGNS&OFFERS"),
                    business_terms=("subsegment", "sales subsegment"),
                ),
                ColumnDefinition(
                    name="booked_pax",
                    type="BIGINT",
                    description="Number of booked passengers.",
                    examples=("30",),
                    business_terms=(
                        "passengers",
                        "pax",
                        "booked passengers",
                        "passenger volume",
                    ),
                ),
                ColumnDefinition(
                    name="net_revenue",
                    type="DOUBLE",
                    description="Net revenue amount from the booking records.",
                    examples=("1844.31",),
                    business_terms=(
                        "sales",
                        "revenue",
                        "net revenue",
                    ),
                ),
            ),
        ),
    ),
    relationships=(),
    example_questions=(
        "Show booked passengers by route since 2025.",
        "What is net revenue by market area?",
        "Show monthly net revenue by booking date.",
        "Which sales planning segments have the highest booked passengers?",
        "Tell me the number of pax on HEL-STO for the departure month of April 2026.",
    ),
    example_sql=(
        "SELECT route_code, SUM(booked_pax) AS booked_passengers FROM sales_figures_since_2025 GROUP BY route_code ORDER BY booked_passengers DESC LIMIT 10",
        "SELECT market_area, SUM(net_revenue) AS net_revenue FROM sales_figures_since_2025 GROUP BY market_area ORDER BY net_revenue DESC LIMIT 10",
        "SELECT date_trunc('month', booking_date) AS booking_month, SUM(net_revenue) AS net_revenue FROM sales_figures_since_2025 GROUP BY booking_month ORDER BY booking_month LIMIT 24",
        "SELECT sales_planning_segment, SUM(booked_pax) AS booked_passengers FROM sales_figures_since_2025 GROUP BY sales_planning_segment ORDER BY booked_passengers DESC LIMIT 10",
        "SELECT SUM(booked_pax) AS booked_pax FROM sales_figures_since_2025 WHERE route_direction = 'HEL-STO' AND departure_date >= DATE '2026-04-01' AND departure_date < DATE '2026-05-01'",
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

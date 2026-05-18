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


DEFAULT_DATA_CATALOG = DataCatalog(
    description=(
        "Central catalog for the single Question & Answer Text-to-SQL workflow. "
        "Create backend/app/catalog_private.py locally to register private data."
    ),
    tables=(),
    relationships=(),
    example_questions=(),
    example_sql=(),
)


def load_data_catalog() -> DataCatalog:
    try:
        from app.catalog_private import DATA_CATALOG as private_catalog
    except ModuleNotFoundError as error:
        if error.name != "app.catalog_private":
            raise
        return DEFAULT_DATA_CATALOG

    return private_catalog


DATA_CATALOG = load_data_catalog()


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

    if catalog.tables:
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
    else:
        lines.append("- None configured.")

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
    if catalog.example_questions:
        lines.extend(f"- {question}" for question in catalog.example_questions)
    else:
        lines.append("- None configured.")

    lines.extend(["", "Example SQL:"])
    if catalog.example_sql:
        lines.extend(f"- {sql}" for sql in catalog.example_sql)
    else:
        lines.append("- None configured.")

    return "\n".join(lines)

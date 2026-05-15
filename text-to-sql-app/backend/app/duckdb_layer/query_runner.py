import re
from pathlib import Path
from typing import Any

import duckdb

from app.duckdb_layer.connection import create_connection
from app.duckdb_layer.sql_validator import validate_sql
from app.modules.registry import get_module_config

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class QueryRunnerError(RuntimeError):
    pass


class MissingDataFileError(QueryRunnerError):
    pass


class InvalidQueryError(QueryRunnerError):
    pass


class EmptyQueryResultError(QueryRunnerError):
    pass


def run_query(module_id: str, sql: str) -> list[dict[str, Any]]:
    module = get_module_config(module_id)
    validated_sql = validate_sql(sql)
    parquet_path = resolve_data_path(module.data_path)

    if not parquet_path.exists():
        raise MissingDataFileError(f"Parquet file not found for module '{module_id}': {module.data_path}")

    assert_valid_identifier(module.table_name)

    connection = create_connection()
    try:
        register_parquet_view(connection, module.table_name, parquet_path)
        result = connection.execute(validated_sql)
        rows = result.fetchall()
        columns = [column[0] for column in result.description]
    except duckdb.Error as error:
        raise InvalidQueryError(f"Invalid SQL for module '{module_id}': {error}") from error
    finally:
        connection.close()

    if not rows:
        raise EmptyQueryResultError(f"Query returned no rows for module '{module_id}'.")

    return [dict(zip(columns, row, strict=True)) for row in rows]


def resolve_data_path(data_path: str) -> Path:
    path = Path(data_path)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def register_parquet_view(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    parquet_path: Path,
) -> None:
    escaped_path = str(parquet_path).replace("'", "''")
    connection.execute(
        f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{escaped_path}')"
    )


def assert_valid_identifier(identifier: str) -> None:
    if not VALID_IDENTIFIER.match(identifier):
        raise InvalidQueryError(f"Invalid DuckDB table identifier: {identifier}")

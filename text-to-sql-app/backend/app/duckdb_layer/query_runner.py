import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import duckdb

from app.catalog import get_allowed_table_names, get_data_catalog
from app.duckdb_layer.connection import create_connection
from app.duckdb_layer.sql_validator import SQLValidationError, validate_sql

PROJECT_ROOT = Path(__file__).resolve().parents[3]
VALID_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
MAX_RETURNED_ROWS = 100


@dataclass(frozen=True)
class QueryExecutionRequest:
    query_id: str
    purpose: str
    sql: str


@dataclass(frozen=True)
class QueryExecutionResult:
    query_id: str
    purpose: str
    sql: str
    rows: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def to_response_payload(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "purpose": self.purpose,
            "sql": self.sql,
            "rows": self.rows,
            "warnings": self.warnings,
        }


class QueryRunnerError(RuntimeError):
    pass


class MissingDataFileError(QueryRunnerError):
    pass


class InvalidQueryError(QueryRunnerError):
    pass


class EmptyQueryResultError(QueryRunnerError):
    pass


def run_query(sql: str) -> list[dict[str, Any]]:
    result = run_queries(
        [
            QueryExecutionRequest(
                query_id="main",
                purpose="Execute a single validated SQL query.",
                sql=sql,
            )
        ]
    )[0]

    return result.rows


def run_queries(queries: list[QueryExecutionRequest]) -> list[QueryExecutionResult]:
    if not queries:
        raise InvalidQueryError("At least one query is required.")

    catalog = get_data_catalog()
    allowed_table_names = get_allowed_table_names()
    validated_queries: list[QueryExecutionRequest] = []

    for query in queries:
        validated_sql = normalize_sql(query.sql)
        try:
            validate_sql(validated_sql, allowed_table_names=allowed_table_names)
        except SQLValidationError as error:
            raise InvalidQueryError(
                f"Invalid SQL for query '{query.query_id}': {error}"
            ) from error

        validated_queries.append(
            QueryExecutionRequest(
                query_id=query.query_id,
                purpose=query.purpose,
                sql=validated_sql,
            )
        )

    for table in catalog.tables:
        assert_valid_identifier(table.table_name)
        parquet_path = resolve_data_path(table.data_path)
        if not parquet_path.exists():
            raise MissingDataFileError(
                f"Parquet file not found for catalog table '{table.table_name}': {table.data_path}"
            )

    connection = create_connection()
    try:
        for table in catalog.tables:
            register_parquet_view(
                connection,
                table.table_name,
                resolve_data_path(table.data_path),
            )
        query_results = []
        for query in validated_queries:
            result = connection.execute(limit_query(query.sql))
            rows = result.fetchall()
            columns = [column[0] for column in result.description]
            mapped_rows = [dict(zip(columns, row, strict=True)) for row in rows]
            warnings = []

            if not mapped_rows:
                warnings.append(f"Query '{query.query_id}' returned no rows.")

            query_results.append(
                QueryExecutionResult(
                    query_id=query.query_id,
                    purpose=query.purpose,
                    sql=query.sql,
                    rows=mapped_rows,
                    warnings=warnings,
                )
            )
    except duckdb.Error as error:
        raise InvalidQueryError(f"Invalid SQL for data catalog: {error}") from error
    finally:
        connection.close()

    return query_results


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


def normalize_sql(sql: str) -> str:
    return sql.strip().rstrip(";")


def limit_query(sql: str) -> str:
    return f"SELECT * FROM ({sql}) AS validated_query LIMIT {MAX_RETURNED_ROWS}"

import pytest

from app.duckdb_layer.query_runner import MAX_RETURNED_ROWS, limit_query
from app.duckdb_layer.sql_validator import SQLValidationError, validate_sql


ALLOWED_TABLES = ["qa"]


def test_valid_select_passes() -> None:
    validate_sql("SELECT * FROM qa LIMIT 10", ALLOWED_TABLES)


def test_valid_with_select_passes() -> None:
    validate_sql(
        """
        WITH recent AS (
            SELECT * FROM qa LIMIT 10
        )
        SELECT * FROM recent LIMIT 5
        """,
        ALLOWED_TABLES,
    )


def test_drop_table_fails() -> None:
    with pytest.raises(SQLValidationError, match="DROP statements are not allowed"):
        validate_sql("DROP TABLE qa", ALLOWED_TABLES)


def test_delete_fails() -> None:
    with pytest.raises(SQLValidationError, match="DELETE statements are not allowed"):
        validate_sql("DELETE FROM qa", ALLOWED_TABLES)


def test_select_from_unknown_table_fails() -> None:
    with pytest.raises(SQLValidationError, match="Table 'unknown_table' is not allowed"):
        validate_sql("SELECT * FROM unknown_table LIMIT 10", ALLOWED_TABLES)


def test_multiple_statements_fail() -> None:
    with pytest.raises(SQLValidationError, match="Only one SQL statement is allowed"):
        validate_sql("SELECT * FROM qa LIMIT 10; SELECT * FROM qa LIMIT 10", ALLOWED_TABLES)


def test_read_parquet_function_fails() -> None:
    with pytest.raises(SQLValidationError, match="read_parquet"):
        validate_sql("SELECT * FROM read_parquet('data/qa/qa.parquet')", ALLOWED_TABLES)


def test_query_without_limit_is_wrapped_with_max_limit() -> None:
    wrapped_query = limit_query("SELECT * FROM qa")

    assert wrapped_query == f"SELECT * FROM (SELECT * FROM qa) AS validated_query LIMIT {MAX_RETURNED_ROWS}"

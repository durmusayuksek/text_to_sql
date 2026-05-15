from collections.abc import Sequence

import sqlglot
from sqlglot import exp

BLOCKED_COMMANDS = {
    "ALTER",
    "ATTACH",
    "COPY",
    "CREATE",
    "DELETE",
    "DETACH",
    "DROP",
    "EXPORT",
    "INSERT",
    "INSTALL",
    "LOAD",
    "MERGE",
    "PRAGMA",
    "REPLACE",
    "TRUNCATE",
    "UPDATE",
}
BLOCKED_FUNCTIONS = {
    "glob",
    "read_csv",
    "read_json",
    "read_parquet",
}
BLOCKED_PATH_MARKERS = ("http://", "https://", "s3://", "httpfs")


class SQLValidationError(ValueError):
    pass


def validate_sql(sql: str, allowed_table_names: Sequence[str]) -> None:
    cleaned_sql = sql.strip()

    if not cleaned_sql:
        raise SQLValidationError("SQL cannot be empty.")

    parsed_expressions = parse_sql(cleaned_sql)

    if len(parsed_expressions) != 1:
        raise SQLValidationError("Only one SQL statement is allowed.")

    expression = parsed_expressions[0]
    first_keyword = get_first_keyword(cleaned_sql)

    if first_keyword in BLOCKED_COMMANDS:
        raise SQLValidationError(f"{first_keyword} statements are not allowed.")

    if not isinstance(expression, exp.Select):
        raise SQLValidationError("Only SELECT queries are allowed.")

    validate_blocked_functions(expression)
    validate_table_access(expression, allowed_table_names)


def parse_sql(sql: str) -> list[exp.Expression]:
    try:
        return sqlglot.parse(sql, read="duckdb")
    except sqlglot.errors.ParseError as error:
        raise SQLValidationError(f"SQL could not be parsed: {error}") from error


def get_first_keyword(sql: str) -> str:
    return sql.lstrip().split(maxsplit=1)[0].rstrip(";").upper()


def validate_blocked_functions(expression: exp.Expression) -> None:
    for function in expression.find_all(exp.Func):
        function_name = function.sql_name().lower()

        if function_name in BLOCKED_FUNCTIONS:
            raise SQLValidationError(f"Function '{function_name}' is not allowed.")

    lowered_sql = expression.sql(dialect="duckdb").lower()

    for marker in BLOCKED_PATH_MARKERS:
        if marker in lowered_sql:
            raise SQLValidationError(f"External file or network access is not allowed: {marker}")


def validate_table_access(
    expression: exp.Expression,
    allowed_table_names: Sequence[str],
) -> None:
    allowed_tables = {table_name.lower() for table_name in allowed_table_names}
    cte_names = get_cte_names(expression)

    for table in expression.find_all(exp.Table):
        table_name = table.name.lower()

        if table_name in cte_names:
            continue

        if table_name not in allowed_tables:
            allowed_values = ", ".join(sorted(allowed_tables))
            raise SQLValidationError(
                f"Table '{table.name}' is not allowed. Allowed tables: {allowed_values}."
            )


def get_cte_names(expression: exp.Expression) -> set[str]:
    with_expression = expression.args.get("with_")

    if not with_expression:
        return set()

    return {
        cte.alias_or_name.lower()
        for cte in with_expression.expressions
        if cte.alias_or_name
    }

def validate_sql(sql: str) -> str:
    if not sql.strip():
        raise ValueError("SQL cannot be empty.")

    return sql


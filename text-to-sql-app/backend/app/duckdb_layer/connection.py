from pathlib import Path

import duckdb


def create_connection(database_path: Path | str = ":memory:") -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(database_path))

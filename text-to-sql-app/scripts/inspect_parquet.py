import argparse
import re
from pathlib import Path
from typing import Any

import duckdb

IDENTIFIER_PATTERN = re.compile(r"(^|_)(id|key|uuid|guid|number|no)$", re.IGNORECASE)
DATE_PATTERN = re.compile(r"(date|time|timestamp|created|updated|departure|booking)", re.IGNORECASE)
NUMERIC_TYPES = {
    "BIGINT",
    "DECIMAL",
    "DOUBLE",
    "FLOAT",
    "HUGEINT",
    "INTEGER",
    "REAL",
    "SMALLINT",
    "TINYINT",
    "UBIGINT",
    "UINTEGER",
    "USMALLINT",
    "UTINYINT",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect a Parquet file before adding it to the data catalog.",
    )
    parser.add_argument("parquet_path", help="Path to a Parquet file.")
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=5,
        help="Number of sample rows to print. Defaults to 5.",
    )
    args = parser.parse_args()

    parquet_path = Path(args.parquet_path)
    if not parquet_path.exists():
        raise SystemExit(f"Parquet file not found: {parquet_path}")

    inspect_parquet(parquet_path, sample_rows=args.sample_rows)


def inspect_parquet(parquet_path: Path, sample_rows: int) -> None:
    escaped_path = str(parquet_path).replace("'", "''")
    connection = duckdb.connect(database=":memory:")
    try:
        row_count = connection.execute(
            f"SELECT COUNT(*) AS row_count FROM read_parquet('{escaped_path}')"
        ).fetchone()[0]
        schema_rows = connection.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{escaped_path}')"
        ).fetchall()
        sample = connection.execute(
            f"SELECT * FROM read_parquet('{escaped_path}') LIMIT ?",
            [sample_rows],
        ).fetchall()
        sample_columns = [
            column[0]
            for column in connection.description
        ]
        null_counts = get_null_counts(connection, escaped_path, schema_rows)
    finally:
        connection.close()

    column_profiles = [
        {
            "name": name,
            "type": column_type,
            "null_count": null_counts[name],
            "possible_identifier": is_possible_identifier(name),
            "possible_date": is_possible_date(name, column_type),
            "possible_numeric_measure": is_possible_numeric_measure(name, column_type),
        }
        for name, column_type, *_ in schema_rows
    ]

    print(f"File: {parquet_path}")
    print(f"Row count: {row_count}")
    print("")
    print("Columns:")
    for profile in column_profiles:
        flags = [
            flag
            for flag, enabled in [
                ("possible identifier", profile["possible_identifier"]),
                ("possible date", profile["possible_date"]),
                ("possible numeric measure", profile["possible_numeric_measure"]),
            ]
            if enabled
        ]
        suffix = f" ({'; '.join(flags)})" if flags else ""
        print(
            f"- {profile['name']} [{profile['type']}], "
            f"nulls: {profile['null_count']}{suffix}"
        )

    print("")
    print(f"Sample rows ({len(sample)}):")
    for row in sample:
        print(dict(zip(sample_columns, row, strict=True)))


def get_null_counts(
    connection: duckdb.DuckDBPyConnection,
    escaped_path: str,
    schema_rows: list[tuple[Any, ...]],
) -> dict[str, int]:
    expressions = [
        f"SUM(CASE WHEN \"{name}\" IS NULL THEN 1 ELSE 0 END) AS \"{name}\""
        for name, *_ in schema_rows
    ]
    query = f"SELECT {', '.join(expressions)} FROM read_parquet('{escaped_path}')"
    row = connection.execute(query).fetchone()

    return {
        name: int(row[index])
        for index, (name, *_) in enumerate(schema_rows)
    }


def is_possible_identifier(column_name: str) -> bool:
    return bool(IDENTIFIER_PATTERN.search(column_name))


def is_possible_date(column_name: str, column_type: str) -> bool:
    return "DATE" in column_type.upper() or "TIMESTAMP" in column_type.upper() or bool(
        DATE_PATTERN.search(column_name)
    )


def is_possible_numeric_measure(column_name: str, column_type: str) -> bool:
    if is_possible_identifier(column_name):
        return False

    return column_type.upper().split("(", maxsplit=1)[0] in NUMERIC_TYPES


if __name__ == "__main__":
    main()

import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "inspect_parquet.py"
SPEC = importlib.util.spec_from_file_location("inspect_parquet", SCRIPT_PATH)
inspect_parquet = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(inspect_parquet)


def test_inspect_parquet_column_classification_helpers() -> None:
    assert inspect_parquet.is_possible_identifier("booking_id")
    assert inspect_parquet.is_possible_identifier("client_key")
    assert inspect_parquet.is_possible_date("departure_date", "VARCHAR")
    assert inspect_parquet.is_possible_date("created_at", "TIMESTAMP")
    assert inspect_parquet.is_possible_numeric_measure("net_sales", "DECIMAL(10,2)")
    assert not inspect_parquet.is_possible_numeric_measure("client_id", "INTEGER")

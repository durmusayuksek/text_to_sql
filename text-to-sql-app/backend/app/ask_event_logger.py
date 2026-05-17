import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.config import Settings
from app.duckdb_layer.query_runner import QueryExecutionResult

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_ask_event(event: dict[str, Any], settings: Settings) -> None:
    if not settings.enable_ask_event_logging:
        return

    try:
        log_path = resolve_log_path(settings.ask_event_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(to_jsonable(event), ensure_ascii=False) + "\n")
    except Exception:
        # Logging must never affect the API response path.
        return


def resolve_log_path(configured_path: str) -> Path:
    path = Path(configured_path)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def build_query_result_summaries(
    query_results: list[QueryExecutionResult],
    include_rows: bool,
) -> list[dict[str, Any]]:
    summaries = []

    for query_result in query_results:
        summary: dict[str, Any] = {
            "query_id": query_result.query_id,
            "purpose": query_result.purpose,
            "sql": query_result.sql,
            "row_count": len(query_result.rows),
            "columns": query_result.columns,
            "warnings": query_result.warnings,
        }

        if include_rows:
            summary["rows"] = query_result.rows

        summaries.append(summary)

    return summaries


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return to_jsonable(asdict(value))

    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set):
        return [to_jsonable(item) for item in value]

    if isinstance(value, datetime | date):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, str | int | float | bool) or value is None:
        return value

    return str(value)

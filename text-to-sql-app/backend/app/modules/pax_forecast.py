from collections.abc import Mapping
from typing import Any

from app.modules.registry import ProcessorResult


def process(
    data: Mapping[str, Any],
    question: str,
    context: Mapping[str, Any],
) -> ProcessorResult:
    """Return a mocked pax forecast result until real business logic exists."""
    return ProcessorResult(
        answer="This is a mocked business answer for the Pax Forecast module.",
        sql="SELECT * FROM sample_table LIMIT 10",
        explanation="This mocked query returns sample rows for pax forecast analysis.",
        data=[
            {"metric": "forecast_pax", "value": 1840, "unit": "passengers"},
            {"metric": "capacity_fill", "value": 0.87, "unit": "ratio"},
            {"metric": "sample_rows", "value": 10, "unit": "count"},
        ],
    )

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
        sql=(
            "SELECT pf.departure_date, pf.route, pf.forecast_pax, pf.capacity, "
            "pf.load_factor, rt.target_load_factor, rt.priority "
            "FROM pax_forecast pf "
            "JOIN pax_route_targets rt ON pf.route = rt.route "
            "LIMIT 10"
        ),
        explanation="This mocked query joins forecast rows to route-level target metadata.",
        data=[],
    )

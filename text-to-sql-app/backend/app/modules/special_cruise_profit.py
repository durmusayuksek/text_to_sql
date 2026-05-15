from collections.abc import Mapping
from typing import Any

from app.modules.registry import ProcessorResult


def process(
    data: Mapping[str, Any],
    question: str,
    context: Mapping[str, Any],
) -> ProcessorResult:
    """Return a mocked profit calculation result until real logic exists."""
    return ProcessorResult(
        answer="This is a mocked business answer for special cruise profit calculation.",
    )

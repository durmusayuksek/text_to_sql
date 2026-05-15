from collections.abc import Mapping
from typing import Any

from app.modules.registry import ProcessorResult


def process(
    data: Mapping[str, Any],
    question: str,
    context: Mapping[str, Any],
) -> ProcessorResult:
    """Return a mocked general QA result until real logic exists."""
    return ProcessorResult(
        answer="This is a mocked business answer for the Questions / Answers module.",
        sql="SELECT * FROM qa LIMIT 10",
        explanation="This mocked query returns sample rows for general analysis.",
        data=[],
    )

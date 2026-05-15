from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

ModuleId = Literal["pax_forecast", "special_cruise_profit", "qa"]


@dataclass(frozen=True)
class TableDefinition:
    name: str
    description: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class ProcessorResult:
    answer: str
    sql: str
    explanation: str
    data: list[dict[str, Any]]


ProcessorFunction = Callable[
    [Mapping[str, Any], str, Mapping[str, Any]],
    ProcessorResult,
]


@dataclass(frozen=True)
class ModuleConfig:
    module_id: ModuleId
    label: str
    description: str
    data_path: str
    table_definitions: tuple[TableDefinition, ...]
    processor_function: ProcessorFunction
    example_questions: tuple[str, ...]


# Processor imports live below shared registry types so processor files can use
# ProcessorResult without creating an import cycle.
from app.modules import pax_forecast, qa, special_cruise_profit


MODULE_REGISTRY: dict[ModuleId, ModuleConfig] = {
    "pax_forecast": ModuleConfig(
        module_id="pax_forecast",
        label="Pax Forecast",
        description="Ask forecasting questions about demand, occupancy, and passenger volume trends.",
        data_path="data/pax_forecast",
        table_definitions=(
            TableDefinition(
                name="pax_forecast",
                description="Placeholder table for passenger forecast inputs.",
                columns=("departure_date", "route", "forecast_pax", "capacity"),
            ),
        ),
        processor_function=pax_forecast.process,
        example_questions=(
            "Which sailings are forecast to exceed capacity targets next month?",
            "Show forecasted passenger volume by route.",
        ),
    ),
    "special_cruise_profit": ModuleConfig(
        module_id="special_cruise_profit",
        label="Special Cruise / Entertainment Profit Calculation",
        description="Explore revenue, cost, margin, and profitability scenarios for special cruise events.",
        data_path="data/special_cruise",
        table_definitions=(
            TableDefinition(
                name="special_cruise_profit",
                description="Placeholder table for event revenue and cost inputs.",
                columns=("event_id", "ticket_revenue", "entertainment_cost", "margin"),
            ),
        ),
        processor_function=special_cruise_profit.process,
        example_questions=(
            "What attendance level is needed to break even?",
            "Which entertainment events have the strongest mocked margin?",
        ),
    ),
    "qa": ModuleConfig(
        module_id="qa",
        label="Questions / Answers",
        description="Use a general analytical workspace for direct questions over prepared datasets.",
        data_path="data/qa",
        table_definitions=(
            TableDefinition(
                name="qa_reference",
                description="Placeholder table for general question answering inputs.",
                columns=("topic", "metric", "value", "updated_at"),
            ),
        ),
        processor_function=qa.process,
        example_questions=(
            "Summarize the most important operational signal.",
            "Rank the available sample metrics.",
        ),
    ),
}


class UnknownModuleError(ValueError):
    pass


def get_registered_modules() -> list[ModuleConfig]:
    return list(MODULE_REGISTRY.values())


def get_module_config(module_id: str) -> ModuleConfig:
    try:
        return MODULE_REGISTRY[module_id]  # type: ignore[index]
    except KeyError as error:
        valid_values = ", ".join(sorted(MODULE_REGISTRY))
        raise UnknownModuleError(
            f"Unknown module_id '{module_id}'. Expected one of: {valid_values}."
        ) from error

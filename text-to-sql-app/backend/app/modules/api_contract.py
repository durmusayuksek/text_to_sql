from app.duckdb_layer.sql_validator import validate_sql
from app.schemas.api import AskRequest, AskResponse, ModuleConfig, ModuleId


MODULES: tuple[ModuleConfig, ...] = (
    ModuleConfig(
        id="pax_forecast",
        title="Pax Forecast",
        description="Ask forecasting questions about demand, occupancy, and passenger volume trends.",
        data_focus="Forecasting",
        accent="teal",
    ),
    ModuleConfig(
        id="special_cruise_profit",
        title="Special Cruise / Entertainment Profit Calculation",
        description="Explore revenue, cost, margin, and profitability scenarios for special cruise events.",
        data_focus="Profit analysis",
        accent="indigo",
    ),
    ModuleConfig(
        id="qa",
        title="Questions / Answers",
        description="Use a general analytical workspace for direct questions over prepared datasets.",
        data_focus="Operations Q&A",
        accent="amber",
    ),
)


class UnknownModuleError(ValueError):
    pass


def get_modules() -> list[ModuleConfig]:
    return list(MODULES)


def build_mock_answer(request: AskRequest) -> AskResponse:
    module_id = validate_module_id(request.module_id)
    validate_question(request.question)
    sql = validate_sql("SELECT * FROM sample_table LIMIT 10")

    return AskResponse(
        answer="This is a mocked business answer for the selected module.",
        sql=sql,
        explanation="This mocked query returns sample rows.",
        data=[
            {"metric": "sample_revenue", "value": 125000, "unit": "SEK"},
            {"metric": "sample_margin", "value": 0.32, "unit": "ratio"},
            {"metric": "sample_rows", "value": 10, "unit": "count"},
        ],
        module_id=module_id,
    )


def validate_module_id(module_id: str) -> ModuleId:
    valid_module_ids = {module.id for module in MODULES}

    if module_id not in valid_module_ids:
        valid_values = ", ".join(sorted(valid_module_ids))
        raise UnknownModuleError(f"Unknown module_id '{module_id}'. Expected one of: {valid_values}.")

    return module_id  # type: ignore[return-value]


def validate_question(question: str) -> None:
    if not question.strip():
        raise ValueError("Question cannot be empty.")

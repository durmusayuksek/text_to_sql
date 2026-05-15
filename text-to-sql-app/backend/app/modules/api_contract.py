from typing import Any

from app.duckdb_layer.query_runner import run_query
from app.duckdb_layer.sql_validator import validate_sql
from app.modules.registry import (
    ModuleConfig as RegistryModuleConfig,
)
from app.modules.registry import (
    UnknownModuleError,
    get_module_config,
    get_registered_modules,
)
from app.schemas.api import AskRequest, AskResponse, ModuleConfig, TableDefinition


def get_modules() -> list[ModuleConfig]:
    return [to_api_module_config(module) for module in get_registered_modules()]


def build_mock_answer(request: AskRequest) -> AskResponse:
    validate_question(request.question)
    module = get_module_config(request.module_id)
    result = module.processor_function(
        data={},
        question=request.question.strip(),
        context=build_processor_context(module),
    )
    sql = validate_sql(result.sql)
    rows = run_query(module.module_id, sql)

    return AskResponse(
        answer=result.answer,
        sql=sql,
        explanation=result.explanation,
        data=rows,
        module_id=module.module_id,
    )


def validate_question(question: str) -> None:
    if not question.strip():
        raise ValueError("Question cannot be empty.")


def to_api_module_config(module: RegistryModuleConfig) -> ModuleConfig:
    return ModuleConfig(
        module_id=module.module_id,
        label=module.label,
        description=module.description,
        data_path=module.data_path,
        table_name=module.table_name,
        table_definitions=[
            TableDefinition(
                name=table.name,
                description=table.description,
                columns=list(table.columns),
            )
            for table in module.table_definitions
        ],
        example_questions=list(module.example_questions),
    )


def build_processor_context(module: RegistryModuleConfig) -> dict[str, Any]:
    return {
        "module_id": module.module_id,
        "label": module.label,
        "table_name": module.table_name,
        "table_definitions": module.table_definitions,
        "example_questions": module.example_questions,
    }

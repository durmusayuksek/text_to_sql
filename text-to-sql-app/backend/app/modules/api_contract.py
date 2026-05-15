import re
from typing import Any

from app.agents.query_agent import generate_sql
from app.config import refresh_settings
from app.duckdb_layer.query_runner import run_query
from app.modules.registry import (
    ModuleConfig as RegistryModuleConfig,
)
from app.modules.registry import (
    UnknownModuleError,
    get_module_config,
    get_registered_modules,
)
from app.schemas.api import (
    AskRequest,
    AskResponse,
    ColumnDefinition,
    ModuleConfig,
    RelationshipDefinition,
    TableDefinition,
)

DESTRUCTIVE_INTENT_PATTERN = re.compile(
    r"\b(delete|update|drop|alter|insert|overwrite|remove|erase|truncate)\b",
    re.IGNORECASE,
)


class DestructiveIntentError(ValueError):
    pass


def get_modules() -> list[ModuleConfig]:
    return [to_api_module_config(module) for module in get_registered_modules()]


def build_mock_answer(request: AskRequest) -> AskResponse:
    validate_question(request.question)
    validate_safe_question_intent(request.question)
    settings = refresh_settings()
    module = get_module_config(request.module_id)
    query_agent_result = generate_sql(module.module_id, request.question.strip())
    sql = query_agent_result.sql.strip().rstrip(";")
    rows = run_query(module.module_id, sql)
    processor_result = module.processor_function(
        data={"rows": rows},
        question=request.question.strip(),
        context=build_processor_context(module, query_agent_result.schema_context_used),
    )

    return AskResponse(
        answer=processor_result.answer,
        sql=sql,
        explanation=query_agent_result.explanation,
        data=rows,
        module_id=module.module_id,
        query_agent_mode=settings.query_agent_mode,
    )


def validate_question(question: str) -> None:
    if not question.strip():
        raise ValueError("Question cannot be empty.")


def validate_safe_question_intent(question: str) -> None:
    match = DESTRUCTIVE_INTENT_PATTERN.search(question)

    if match:
        raise DestructiveIntentError(
            f"Destructive or modifying requests are not allowed: '{match.group(1)}'. "
            "This app only supports safe read-only analytical questions."
        )


def to_api_module_config(module: RegistryModuleConfig) -> ModuleConfig:
    return ModuleConfig(
        module_id=module.module_id,
        label=module.label,
        description=module.description,
        tables=[
            TableDefinition(
                table_name=table.table_name,
                data_path=table.data_path,
                description=table.description,
                columns=[
                    ColumnDefinition(
                        name=column.name,
                        type=column.type,
                        description=column.description,
                        examples=list(column.examples),
                        business_terms=list(column.business_terms),
                    )
                    for column in table.columns
                ],
            )
            for table in module.tables
        ],
        relationships=[
            RelationshipDefinition(
                left_table=relationship.left_table,
                left_column=relationship.left_column,
                right_table=relationship.right_table,
                right_column=relationship.right_column,
                relationship_type=relationship.relationship_type,
                description=relationship.description,
            )
            for relationship in module.relationships
        ],
        example_questions=list(module.example_questions),
        example_sql=list(module.example_sql),
    )


def build_processor_context(
    module: RegistryModuleConfig,
    schema_context_used: str,
) -> dict[str, Any]:
    return {
        "module_id": module.module_id,
        "label": module.label,
        "tables": module.tables,
        "relationships": module.relationships,
        "example_questions": module.example_questions,
        "example_sql": module.example_sql,
        "schema_context_used": schema_context_used,
    }

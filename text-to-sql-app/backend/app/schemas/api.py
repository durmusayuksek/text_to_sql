from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    app_name: str = Field(serialization_alias="appName")
    status: Literal["ok"]
    environment: str


ModuleId = str


class TableDefinition(BaseModel):
    name: str
    description: str
    columns: list[str]


class ModuleConfig(BaseModel):
    module_id: ModuleId
    label: str
    description: str
    data_path: str
    table_name: str
    table_definitions: list[TableDefinition]
    example_questions: list[str]


class AskRequest(BaseModel):
    module_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sql: str
    explanation: str
    data: list[dict[str, Any]]
    module_id: ModuleId

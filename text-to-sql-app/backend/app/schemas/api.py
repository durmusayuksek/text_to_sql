from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    app_name: str = Field(serialization_alias="appName")
    status: Literal["ok"]
    environment: str


ModuleId = str


class ColumnDefinition(BaseModel):
    name: str
    type: str
    description: str
    examples: list[str] = Field(default_factory=list)
    business_terms: list[str] = Field(default_factory=list)


class TableDefinition(BaseModel):
    table_name: str
    data_path: str
    description: str
    columns: list[ColumnDefinition]


class RelationshipDefinition(BaseModel):
    left_table: str
    left_column: str
    right_table: str
    right_column: str
    relationship_type: str
    description: str


class ModuleConfig(BaseModel):
    module_id: ModuleId
    label: str
    description: str
    tables: list[TableDefinition]
    relationships: list[RelationshipDefinition]
    example_questions: list[str]
    example_sql: list[str]


class AskRequest(BaseModel):
    module_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sql: str
    explanation: str
    data: list[dict[str, Any]]
    module_id: ModuleId
    query_agent_mode: Literal["mock", "openai"]

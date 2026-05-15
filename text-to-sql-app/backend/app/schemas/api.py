from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    app_name: str = Field(serialization_alias="appName")
    status: Literal["ok"]
    environment: str


ModuleId = Literal["pax_forecast", "special_cruise_profit", "qa"]
ModuleAccent = Literal["teal", "indigo", "amber"]


class ModuleConfig(BaseModel):
    id: ModuleId
    title: str
    description: str
    data_focus: str
    accent: ModuleAccent


class AskRequest(BaseModel):
    module_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sql: str
    explanation: str
    data: list[dict[str, Any]]
    module_id: ModuleId

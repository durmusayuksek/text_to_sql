from typing import Literal

from pydantic import BaseModel

from app.schemas.api import ModuleId


class ModuleDefinition(BaseModel):
    name: ModuleId
    display_name: str
    description: str

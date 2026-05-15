from typing import Literal

from pydantic import BaseModel


ModuleName = Literal["pax_forecast", "special_cruise_profit", "qa"]


class ModuleDefinition(BaseModel):
    name: ModuleName
    display_name: str
    description: str


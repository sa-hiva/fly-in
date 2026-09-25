from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Optional
from enum import Enum

class ZoneCategory(Enum):
    START="start"
    REGULAR="regular"
    END="end"

class ZoneType(Enum):
    NORMAL = "normal"
    PRIORITY = "priority"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"

class Zone(BaseModel):
    name: str = Field(min_length=1)
    x: int
    y: int
    zone_type: ZoneType = Field(default=ZoneType.NORMAL)
    color: Optional[str] = Field(default=None)
    max_drones: int = Field(ge=1, default=1)
    zone_category: ZoneCategory = Field(default=ZoneCategory.REGULAR)

    @model_validator(mode='after')
    def validate_model(self) -> 'Zone':
        if " " in self.color:
            raise ValueError("Color must not have spaces.")
        if "-" in self.color:
            raise ValueError("Color must not contain dashes")
        if self.color and not self.color.isalnum():
            raise ValueError("Color must be alphanumeric")
        return self
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from enum import Enum


class ZoneCategory(Enum):
    START = "start"
    REGULAR = "regular"
    END = "end"


class ZoneType(Enum):
    NORMAL = "normal"
    PRIORITY = "priority"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"


class Zone(BaseModel):
    name: str = Field(min_length=1)
    x: int
    y: int
    zone_type: ZoneType = Field(alias="zone", default=ZoneType.NORMAL)
    color: Optional[str] = Field(default=None)
    max_drones: int = Field(ge=1, default=1)
    zone_category: ZoneCategory = Field(default=ZoneCategory.REGULAR)

    @model_validator(mode='after')
    def validate_model(self) -> 'Zone':
        if self.color is not None and not self.color.isalnum():
            raise ValueError("Color must be alphanumeric "
                             "(no spaces or dashes)")
        return self

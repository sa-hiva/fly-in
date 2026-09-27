from pydantic import BaseModel, Field


class Drone(BaseModel):
    id: int = Field(gt=0)

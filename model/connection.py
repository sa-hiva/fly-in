from pydantic import BaseModel, Field, model_validator


class Connection(BaseModel):
    endpoints: frozenset[str]
    max_link_capacity: int = Field(ge=1, default=1)

    @model_validator(mode='after')
    def validate_model(self) -> 'Connection':
        if len(self.endpoints) != 2:
            raise ValueError("Connection must have exactly two endpoints.")
        return self

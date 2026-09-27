from pydantic import BaseModel, Field, model_validator
from model import ZoneNotInConnectionError


class Connection(BaseModel):
    endpoints: frozenset[str]
    max_link_capacity: int = Field(ge=1, default=1)

    @model_validator(mode='after')
    def validate_model(self) -> 'Connection':
        if len(self.endpoints) != 2:
            raise ValueError("Connection must have exactly two endpoints.")
        return self

    def get_connection_end(self, known_zone: str) -> str:
        if known_zone not in self.endpoints:
            raise ZoneNotInConnectionError(known_zone, self.endpoints)
        other = next((z for z in self.endpoints if z != known_zone), None)
        if other is None:
            raise ZoneNotInConnectionError(known_zone, self.endpoints)
        return other
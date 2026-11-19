from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AircraftCreate(BaseModel):
    registration: str = Field(min_length=1, max_length=30)
    manufacturer: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    serial_number: str = Field(min_length=1, max_length=100)


class AircraftResponse(BaseModel):
    id: UUID
    registration: str
    manufacturer: str
    model: str
    serial_number: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

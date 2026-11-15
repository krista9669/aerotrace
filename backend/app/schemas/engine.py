from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EngineCreate(BaseModel):
    serial_number: str = Field(min_length=1, max_length=100)
    manufacturer: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    aircraft_id: UUID | None = None


class EngineResponse(BaseModel):
    id: UUID
    serial_number: str
    manufacturer: str
    model: str
    aircraft_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComponentCreate(BaseModel):
    part_number: str = Field(min_length=1, max_length=100)
    serial_number: str = Field(min_length=1, max_length=100)
    manufacturer: str = Field(min_length=1, max_length=100)
    component_type: str = Field(min_length=1, max_length=100)
    status: str = Field(default="REGISTERED", max_length=50)


class ComponentUpdate(BaseModel):
    part_number: str = Field(min_length=1, max_length=100)
    serial_number: str = Field(min_length=1, max_length=100)
    manufacturer: str = Field(min_length=1, max_length=100)
    component_type: str = Field(min_length=1, max_length=100)
    status: str = Field(min_length=1, max_length=50)


class ComponentResponse(BaseModel):
    id: UUID
    part_number: str
    serial_number: str
    manufacturer: str
    component_type: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

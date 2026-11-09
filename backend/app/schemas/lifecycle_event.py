from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LifecycleEventCreate(BaseModel):
    component_id: UUID
    organisation_id: UUID
    event_type: str = Field(min_length=1, max_length=50)
    description: str | None = None
    performed_by: str = Field(min_length=1, max_length=100)
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")

        return value


class LifecycleEventResponse(BaseModel):
    id: UUID
    component_id: UUID
    organisation_id: UUID
    event_type: str
    description: str | None
    performed_by: str
    occurred_at: datetime
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)

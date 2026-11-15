from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class InstallationCreate(BaseModel):
    component_id: UUID
    engine_id: UUID
    installed_at: datetime
    installation_notes: str | None = None

    @field_validator("installed_at")
    @classmethod
    def validate_installed_at(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("installed_at must include a timezone")
        return value


class InstallationRemoval(BaseModel):
    removed_at: datetime | None = None

    @field_validator("removed_at")
    @classmethod
    def validate_removed_at(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("removed_at must include a timezone")
        return value


class InstallationResponse(BaseModel):
    id: UUID
    component_id: UUID
    engine_id: UUID
    installed_at: datetime
    removed_at: datetime | None
    installation_notes: str | None

    model_config = ConfigDict(from_attributes=True)

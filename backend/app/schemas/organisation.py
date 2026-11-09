from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrganisationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    organisation_type: str = Field(min_length=1, max_length=50)
    code: str = Field(min_length=1, max_length=50)


class OrganisationResponse(BaseModel):
    id: UUID
    name: str
    organisation_type: str
    code: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

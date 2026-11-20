from pydantic import BaseModel

from app.schemas.aircraft import AircraftResponse
from app.schemas.component import ComponentResponse
from app.schemas.engine import EngineResponse
from app.schemas.installation import InstallationResponse
from app.schemas.lifecycle_event import LifecycleEventResponse
from app.schemas.organisation import OrganisationResponse


class LifecycleEventTraceability(BaseModel):
    event: LifecycleEventResponse
    organisation: OrganisationResponse


class ComponentTraceability(BaseModel):
    component: ComponentResponse
    lifecycle_events: list[LifecycleEventTraceability]


class InstallationTraceability(BaseModel):
    installation: InstallationResponse
    component: ComponentTraceability


class EngineTraceability(BaseModel):
    engine: EngineResponse
    installations: list[InstallationTraceability]


class AircraftTraceabilityResponse(BaseModel):
    aircraft: AircraftResponse
    engines: list[EngineTraceability]

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import (
    Aircraft,
    Component,
    Engine,
    Installation,
    LifecycleEvent,
    Organisation,
)
from app.schemas.traceability import AircraftTraceabilityResponse

router = APIRouter(tags=["Traceability"])


@router.get(
    "/aircraft/{aircraft_id}/traceability",
    response_model=AircraftTraceabilityResponse,
    status_code=status.HTTP_200_OK,
)
def get_aircraft_traceability(
    aircraft_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    # 1. Retrieve aircraft
    aircraft = db.get(Aircraft, aircraft_id)

    if aircraft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aircraft not found",
        )

    # 2. Retrieve all engines belonging to the aircraft
    engines = db.scalars(
        select(Engine)
        .where(Engine.aircraft_id == aircraft_id)
        .order_by(Engine.created_at)
    ).all()

    if not engines:
        return {
            "aircraft": aircraft,
            "engines": [],
        }

    engine_ids = [engine.id for engine in engines]

    # 3. Retrieve installation history for these engines
    installations = db.scalars(
        select(Installation)
        .where(Installation.engine_id.in_(engine_ids))
        .order_by(Installation.installed_at.desc())
    ).all()

    if not installations:
        return {
            "aircraft": aircraft,
            "engines": [
                {
                    "engine": engine,
                    "installations": [],
                }
                for engine in engines
            ],
        }

    # 4. Retrieve all components referenced by installations
    component_ids = list({installation.component_id for installation in installations})

    components = db.scalars(
        select(Component).where(Component.id.in_(component_ids))
    ).all()

    components_by_id = {component.id: component for component in components}

    # 5. Retrieve lifecycle events for those components
    events = db.scalars(
        select(LifecycleEvent)
        .where(LifecycleEvent.component_id.in_(component_ids))
        .order_by(
            LifecycleEvent.occurred_at.desc(),
            LifecycleEvent.recorded_at.desc(),
        )
    ).all()

    events_by_component = {}

    for event in events:
        events_by_component.setdefault(event.component_id, []).append(event)

    # 6. Retrieve organisations associated with the lifecycle events
    organisation_ids = list({event.organisation_id for event in events})

    organisations = []

    if organisation_ids:
        organisations = db.scalars(
            select(Organisation).where(Organisation.id.in_(organisation_ids))
        ).all()

    organisations_by_id = {
        organisation.id: organisation for organisation in organisations
    }

    # 7. Construct the component traceability details
    component_traceability = {}

    for component_id, component in components_by_id.items():
        lifecycle_events = []

        for event in events_by_component.get(component_id, []):
            organisation = organisations_by_id.get(event.organisation_id)

            if organisation is not None:
                lifecycle_events.append(
                    {
                        "event": event,
                        "organisation": organisation,
                    }
                )

        component_traceability[component_id] = {
            "component": component,
            "lifecycle_events": lifecycle_events,
        }

    # 8. Group installations under their respective engines
    installations_by_engine = {}

    for installation in installations:
        installations_by_engine.setdefault(installation.engine_id, []).append(
            installation
        )

    engine_traceability = []

    for engine in engines:
        engine_installations = []

        for installation in installations_by_engine.get(engine.id, []):
            component_details = component_traceability.get(installation.component_id)

            if component_details is not None:
                engine_installations.append(
                    {
                        "installation": installation,
                        "component": component_details,
                    }
                )

        engine_traceability.append(
            {
                "engine": engine,
                "installations": engine_installations,
            }
        )

    # 9. Return the complete aircraft traceability hierarchy
    return {
        "aircraft": aircraft,
        "engines": engine_traceability,
    }

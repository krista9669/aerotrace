from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Component, LifecycleEvent, Organisation
from app.schemas.lifecycle_event import (
    LifecycleEventCreate,
    LifecycleEventResponse,
)

router = APIRouter(
    prefix="/lifecycle-events",
    tags=["Lifecycle Events"],
)


@router.post(
    "",
    response_model=LifecycleEventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lifecycle_event(
    event_data: LifecycleEventCreate,
    db: Annotated[Session, Depends(get_db)],
):
    component = db.get(Component, event_data.component_id)

    if component is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )

    organisation = db.get(Organisation, event_data.organisation_id)

    if organisation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organisation not found",
        )

    lifecycle_event = LifecycleEvent(**event_data.model_dump())

    db.add(lifecycle_event)

    try:
        db.commit()
        db.refresh(lifecycle_event)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create lifecycle event due to a database "
            "integrity conflict.",
        ) from None

    return lifecycle_event


@router.get(
    "",
    response_model=list[LifecycleEventResponse],
    status_code=status.HTTP_200_OK,
)
def get_lifecycle_events(
    db: Annotated[Session, Depends(get_db)],
    component_id: Annotated[UUID | None, Query()] = None,
    organisation_id: Annotated[UUID | None, Query()] = None,
    event_type: Annotated[
        str | None,
        Query(min_length=1, max_length=50),
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    statement = select(LifecycleEvent)

    if component_id is not None:
        statement = statement.where(LifecycleEvent.component_id == component_id)

    if organisation_id is not None:
        statement = statement.where(LifecycleEvent.organisation_id == organisation_id)

    if event_type is not None:
        statement = statement.where(LifecycleEvent.event_type == event_type)

    statement = (
        statement.order_by(
            LifecycleEvent.occurred_at.desc(),
            LifecycleEvent.recorded_at.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    events = db.scalars(statement).all()

    return events


@router.get(
    "/{event_id}",
    response_model=LifecycleEventResponse,
    status_code=status.HTTP_200_OK,
)
def get_lifecycle_event(
    event_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    lifecycle_event = db.get(LifecycleEvent, event_id)

    if lifecycle_event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lifecycle event not found",
        )

    return lifecycle_event

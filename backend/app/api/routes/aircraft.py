
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Aircraft
from app.schemas.aircraft import AircraftCreate, AircraftResponse

router = APIRouter(
    prefix="/aircraft",
    tags=["Aircraft"],
)


@router.post(
    "",
    response_model=AircraftResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_aircraft(
    aircraft_data: AircraftCreate,
    db: Annotated[Session, Depends(get_db)],
):
    aircraft = Aircraft(**aircraft_data.model_dump())

    db.add(aircraft)

    try:
        db.commit()
        db.refresh(aircraft)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An aircraft with this registration or serial number already exists."
            ),
        ) from None

    return aircraft


@router.get(
    "",
    response_model=list[AircraftResponse],
    status_code=status.HTTP_200_OK,
)
def get_aircraft_list(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    statement = select(Aircraft).offset(skip).limit(limit)

    aircraft_list = db.scalars(statement).all()

    return aircraft_list


@router.get(
    "/{aircraft_id}",
    response_model=AircraftResponse,
    status_code=status.HTTP_200_OK,
)
def get_aircraft(
    aircraft_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    aircraft = db.get(Aircraft, aircraft_id)

    if aircraft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aircraft not found",
        )

    return aircraft
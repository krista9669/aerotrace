from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Aircraft, Engine
from app.schemas.engine import EngineCreate, EngineResponse

router = APIRouter(
    prefix="/engines",
    tags=["Engines"],
)


@router.post(
    "",
    response_model=EngineResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_engine(
    engine_data: EngineCreate,
    db: Annotated[Session, Depends(get_db)],
):
    if engine_data.aircraft_id is not None:
        aircraft = db.get(Aircraft, engine_data.aircraft_id)

        if aircraft is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aircraft not found",
            )

    engine = Engine(**engine_data.model_dump())

    db.add(engine)

    try:
        db.commit()
        db.refresh(engine)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An engine with this serial number already exists.",
        ) from None

    return engine


@router.get(
    "",
    response_model=list[EngineResponse],
    status_code=status.HTTP_200_OK,
)
def get_engines(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    statement = select(Engine).offset(skip).limit(limit)

    engines = db.scalars(statement).all()

    return engines


@router.get(
    "/{engine_id}",
    response_model=EngineResponse,
    status_code=status.HTTP_200_OK,
)
def get_engine(
    engine_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    engine = db.get(Engine, engine_id)

    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engine not found",
        )

    return engine

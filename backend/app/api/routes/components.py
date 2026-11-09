from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Component
from app.schemas.component import (
    ComponentCreate,
    ComponentResponse,
    ComponentUpdate,
)

router = APIRouter(
    prefix="/components",
    tags=["Components"],
)


@router.post(
    "",
    response_model=ComponentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_component(
    component_data: ComponentCreate,
    db: Annotated[Session, Depends(get_db)],
):
    component = Component(**component_data.model_dump())

    db.add(component)

    try:
        db.commit()
        db.refresh(component)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A component with this manufacturer, part number, "
            "and serial number already exists.",
        ) from None

    return component


@router.get(
    "",
    response_model=list[ComponentResponse],
    status_code=status.HTTP_200_OK,
)
def get_components(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    statement = select(Component).offset(skip).limit(limit)

    components = db.scalars(statement).all()

    return components


@router.get(
    "/{component_id}",
    response_model=ComponentResponse,
    status_code=status.HTTP_200_OK,
)
def get_component(
    component_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    component = db.get(Component, component_id)

    if component is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )

    return component


@router.put(
    "/{component_id}",
    response_model=ComponentResponse,
    status_code=status.HTTP_200_OK,
)
def update_component(
    component_id: UUID,
    component_data: ComponentUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    component = db.get(Component, component_id)

    if component is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )

    for field, value in component_data.model_dump().items():
        setattr(component, field, value)

    try:
        db.commit()
        db.refresh(component)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A component with this manufacturer, part number, "
            "and serial number already exists.",
        ) from None

    return component

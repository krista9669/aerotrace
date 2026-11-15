from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Component, Engine, Installation
from app.schemas.installation import (
    InstallationCreate,
    InstallationRemoval,
    InstallationResponse,
)

router = APIRouter(
    prefix="/installations",
    tags=["Installations"],
)


@router.post(
    "",
    response_model=InstallationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_installation(
    installation_data: InstallationCreate,
    db: Annotated[Session, Depends(get_db)],
):
    component_statement = (
        select(Component)
        .where(Component.id == installation_data.component_id)
        .with_for_update()
    )

    component = db.scalars(component_statement).first()

    if component is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )

    if component.status != "REGISTERED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Component must have REGISTERED status before installation. "
                f"Current status: {component.status}"
            ),
        )

    engine = db.get(Engine, installation_data.engine_id)

    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Engine not found",
        )

    active_statement = select(Installation).where(
        Installation.component_id == installation_data.component_id,
        Installation.removed_at.is_(None),
    )

    active_installation = db.scalars(active_statement).first()

    if active_installation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Component already has an active installation.",
        )

    installation = Installation(**installation_data.model_dump())

    component.status = "INSTALLED"
    db.add(installation)

    try:
        db.commit()
        db.refresh(installation)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Unable to create installation due to a database conflict."),
        ) from None

    return installation


@router.get(
    "",
    response_model=list[InstallationResponse],
    status_code=status.HTTP_200_OK,
)
def get_installations(
    db: Annotated[Session, Depends(get_db)],
    component_id: Annotated[UUID | None, Query()] = None,
    engine_id: Annotated[UUID | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    statement = select(Installation)

    if component_id is not None:
        statement = statement.where(Installation.component_id == component_id)

    if engine_id is not None:
        statement = statement.where(Installation.engine_id == engine_id)

    statement = (
        statement.order_by(Installation.installed_at.desc()).offset(skip).limit(limit)
    )

    installations = db.scalars(statement).all()

    return installations


@router.get(
    "/{installation_id}",
    response_model=InstallationResponse,
    status_code=status.HTTP_200_OK,
)
def get_installation(
    installation_id: UUID,
    db: Annotated[Session, Depends(get_db)],
):
    installation = db.get(Installation, installation_id)

    if installation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation not found",
        )

    return installation


@router.post(
    "/{installation_id}/remove",
    response_model=InstallationResponse,
    status_code=status.HTTP_200_OK,
)
def remove_installation(
    installation_id: UUID,
    removal_data: InstallationRemoval,
    db: Annotated[Session, Depends(get_db)],
):
    installation_statement = (
        select(Installation).where(Installation.id == installation_id).with_for_update()
    )

    installation = db.scalars(installation_statement).first()

    if installation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Installation not found",
        )

    if installation.removed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Component has already been removed.",
        )

    component = db.get(Component, installation.component_id)

    if component is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found",
        )

    removed_at = removal_data.removed_at or datetime.now(UTC)

    if removed_at <= installation.installed_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Removal time must be later than installation time.",
        )

    installation.removed_at = removed_at
    component.status = "REGISTERED"

    try:
        db.commit()
        db.refresh(installation)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=("Unable to remove component due to a database conflict."),
        ) from None

    return installation

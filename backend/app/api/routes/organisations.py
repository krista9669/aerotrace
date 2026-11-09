from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Organisation
from app.schemas.organisation import (
    OrganisationCreate,
    OrganisationResponse,
)

router = APIRouter(
    prefix="/organisations",
    tags=["Organisations"],
)


@router.post(
    "",
    response_model=OrganisationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organisation(
    organisation_data: OrganisationCreate,
    db: Annotated[Session, Depends(get_db)],
):
    organisation = Organisation(**organisation_data.model_dump())

    db.add(organisation)

    try:
        db.commit()
        db.refresh(organisation)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An organisation with this code already exists.",
        ) from None

    return organisation


@router.get(
    "",
    response_model=list[OrganisationResponse],
    status_code=status.HTTP_200_OK,
)
def get_organisations(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    statement = select(Organisation).offset(skip).limit(limit)

    organisations = db.scalars(statement).all()

    return organisations

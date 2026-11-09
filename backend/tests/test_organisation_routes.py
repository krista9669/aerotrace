import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.main import app
from app.models import Organisation

ORGANISATION_ID = uuid.UUID("5146c0bc-4c69-4d89-b677-3b40914be9b1")
CREATED_AT = datetime(2026, 11, 9, 18, 56, 44, tzinfo=UTC)

ORGANISATION_PAYLOAD = {
    "name": "Aero Maintenance Services",
    "organisation_type": "MAINTENANCE",
    "code": "AMS001",
}


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


def make_organisation():
    return Organisation(
        id=ORGANISATION_ID,
        name="Aero Maintenance Services",
        organisation_type="MAINTENANCE",
        code="AMS001",
        created_at=CREATED_AT,
    )


def make_integrity_error():
    return IntegrityError(
        "INSERT",
        {},
        Exception("duplicate organisation code"),
    )


def test_create_organisation_returns_created_organisation(client, db_session):
    def populate_generated_fields(organisation):
        organisation.id = ORGANISATION_ID
        organisation.created_at = CREATED_AT

    db_session.refresh.side_effect = populate_generated_fields

    response = client.post(
        "/organisations",
        json=ORGANISATION_PAYLOAD,
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(ORGANISATION_ID)
    assert response.json()["name"] == "Aero Maintenance Services"
    assert response.json()["organisation_type"] == "MAINTENANCE"
    assert response.json()["code"] == "AMS001"

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()


def test_create_organisation_returns_conflict_for_duplicate(client, db_session):
    db_session.commit.side_effect = make_integrity_error()

    response = client.post(
        "/organisations",
        json=ORGANISATION_PAYLOAD,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An organisation with this code already exists."
    )

    db_session.rollback.assert_called_once()


def test_get_organisations_returns_organisation_list(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_organisation()]

    response = client.get("/organisations?skip=0&limit=100")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(ORGANISATION_ID)
    assert response.json()[0]["code"] == "AMS001"


def test_get_organisations_with_pagination(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_organisation()]

    response = client.get("/organisations?skip=0&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 1
    db_session.scalars.assert_called_once()

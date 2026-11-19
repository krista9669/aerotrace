import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.main import app
from app.models import Aircraft

AIRCRAFT_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789001")
CREATED_AT = datetime(2026, 11, 19, 10, 0, tzinfo=UTC)

AIRCRAFT_PAYLOAD = {
    "registration": "VT-XYZ",
    "manufacturer": "Airbus",
    "model": "A320neo",
    "serial_number": "AIR-2026-002",
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


def make_aircraft():
    return Aircraft(
        id=AIRCRAFT_ID,
        registration="VT-XYZ",
        manufacturer="Airbus",
        model="A320neo",
        serial_number="AIR-2026-002",
        created_at=CREATED_AT,
    )


def make_integrity_error():
    return IntegrityError(
        "INSERT",
        {},
        Exception("duplicate aircraft registration or serial number"),
    )


# --------------------------------------------------
# CREATE AIRCRAFT TESTS
# --------------------------------------------------


def test_create_aircraft_returns_created_aircraft(client, db_session):
    def populate_generated_fields(aircraft):
        aircraft.id = AIRCRAFT_ID
        aircraft.created_at = CREATED_AT

    db_session.refresh.side_effect = populate_generated_fields

    response = client.post(
        "/aircraft",
        json=AIRCRAFT_PAYLOAD,
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(AIRCRAFT_ID)
    assert response.json()["registration"] == "VT-XYZ"
    assert response.json()["manufacturer"] == "Airbus"
    assert response.json()["model"] == "A320neo"
    assert response.json()["serial_number"] == "AIR-2026-002"

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()


def test_create_aircraft_returns_conflict_for_duplicate(client, db_session):
    db_session.commit.side_effect = make_integrity_error()

    response = client.post(
        "/aircraft",
        json=AIRCRAFT_PAYLOAD,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An aircraft with this registration or serial number already exists."
    )

    db_session.rollback.assert_called_once()


def test_create_aircraft_rejects_invalid_payload(client, db_session):
    invalid_payload = {
        **AIRCRAFT_PAYLOAD,
        "registration": "",
    }

    response = client.post(
        "/aircraft",
        json=invalid_payload,
    )

    assert response.status_code == 422
    db_session.add.assert_not_called()


# --------------------------------------------------
# GET AIRCRAFT LIST TESTS
# --------------------------------------------------


def test_get_aircraft_returns_aircraft_list(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_aircraft()]

    response = client.get("/aircraft")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(AIRCRAFT_ID)
    assert response.json()[0]["registration"] == "VT-XYZ"


def test_get_aircraft_supports_pagination(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_aircraft()]

    response = client.get("/aircraft?skip=0&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 1
    db_session.scalars.assert_called_once()


# --------------------------------------------------
# GET INDIVIDUAL AIRCRAFT TESTS
# --------------------------------------------------


def test_get_aircraft_by_id_returns_aircraft(client, db_session):
    db_session.get.return_value = make_aircraft()

    response = client.get(f"/aircraft/{AIRCRAFT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(AIRCRAFT_ID)
    assert response.json()["registration"] == "VT-XYZ"
    assert response.json()["serial_number"] == "AIR-2026-002"


def test_get_aircraft_by_id_returns_404_when_missing(client, db_session):
    db_session.get.return_value = None

    response = client.get(f"/aircraft/{AIRCRAFT_ID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Aircraft not found"

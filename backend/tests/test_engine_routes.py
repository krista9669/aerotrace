import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.main import app
from app.models import Aircraft, Engine

ENGINE_ID = uuid.UUID("91b6f280-4d5d-4fa5-9a29-123456789001")
AIRCRAFT_ID = uuid.UUID("91b6f280-4d5d-4fa5-9a29-123456789002")
CREATED_AT = datetime(2026, 11, 15, 2, 0, tzinfo=UTC)

ENGINE_PAYLOAD = {
    "serial_number": "ENG-2026-001",
    "manufacturer": "CFM International",
    "model": "LEAP-1A",
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
        registration="VT-ABC",
        manufacturer="Airbus",
        model="A320",
        serial_number="AIR-2026-001",
        created_at=CREATED_AT,
    )


def make_engine():
    return Engine(
        id=ENGINE_ID,
        serial_number="ENG-2026-001",
        manufacturer="CFM International",
        model="LEAP-1A",
        aircraft_id=None,
        created_at=CREATED_AT,
    )


def make_integrity_error():
    return IntegrityError(
        "INSERT",
        {},
        Exception("duplicate engine serial number"),
    )


def test_create_engine_without_aircraft_returns_created_engine(client, db_session):
    def populate_generated_fields(engine):
        engine.id = ENGINE_ID
        engine.created_at = CREATED_AT

    db_session.refresh.side_effect = populate_generated_fields

    response = client.post(
        "/engines",
        json=ENGINE_PAYLOAD,
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(ENGINE_ID)
    assert response.json()["serial_number"] == "ENG-2026-001"
    assert response.json()["manufacturer"] == "CFM International"
    assert response.json()["model"] == "LEAP-1A"
    assert response.json()["aircraft_id"] is None

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()


def test_create_engine_with_existing_aircraft(client, db_session):
    db_session.get.return_value = make_aircraft()

    def populate_generated_fields(engine):
        engine.id = ENGINE_ID
        engine.created_at = CREATED_AT

    db_session.refresh.side_effect = populate_generated_fields

    payload = {
        **ENGINE_PAYLOAD,
        "aircraft_id": str(AIRCRAFT_ID),
    }

    response = client.post("/engines", json=payload)

    assert response.status_code == 201
    assert response.json()["aircraft_id"] == str(AIRCRAFT_ID)
    db_session.get.assert_called_once_with(Aircraft, AIRCRAFT_ID)
    db_session.add.assert_called_once()


def test_create_engine_returns_404_when_aircraft_missing(client, db_session):
    db_session.get.return_value = None

    payload = {
        **ENGINE_PAYLOAD,
        "aircraft_id": str(AIRCRAFT_ID),
    }

    response = client.post("/engines", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Aircraft not found"
    db_session.add.assert_not_called()


def test_create_engine_returns_conflict_for_duplicate_serial_number(client, db_session):
    db_session.commit.side_effect = make_integrity_error()

    response = client.post(
        "/engines",
        json=ENGINE_PAYLOAD,
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "An engine with this serial number already exists."
    )

    db_session.rollback.assert_called_once()


def test_get_engines_returns_engine_list(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_engine()]

    response = client.get("/engines")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(ENGINE_ID)
    assert response.json()[0]["serial_number"] == "ENG-2026-001"


def test_get_engines_supports_pagination(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_engine()]

    response = client.get("/engines?skip=0&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 1
    db_session.scalars.assert_called_once()


def test_get_engine_returns_engine(client, db_session):
    db_session.get.return_value = make_engine()

    response = client.get(f"/engines/{ENGINE_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(ENGINE_ID)
    assert response.json()["serial_number"] == "ENG-2026-001"


def test_get_engine_returns_404_when_missing(client, db_session):
    db_session.get.return_value = None

    response = client.get(f"/engines/{ENGINE_ID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Engine not found"

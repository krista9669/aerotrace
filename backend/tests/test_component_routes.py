import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core import database
from app.core.database import get_db
from app.main import app
from app.models import Component
from app.models.entities import utc_now

COMPONENT_ID = uuid.UUID("5487c281-4473-42b5-8fbf-4a1a3fac669c")
CREATED_AT = datetime(2026, 11, 9, 7, 30, 17, tzinfo=UTC)

COMPONENT_PAYLOAD = {
    "part_number": "PN-1001",
    "serial_number": "SN-2026-001",
    "manufacturer": "Airbus",
    "component_type": "HYDRAULIC_PUMP",
    "status": "REGISTERED",
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


def make_component():
    return Component(
        id=COMPONENT_ID,
        part_number="PN-1001",
        serial_number="SN-2026-001",
        manufacturer="Airbus",
        component_type="HYDRAULIC_PUMP",
        status="REGISTERED",
        created_at=CREATED_AT,
    )


def make_integrity_error():
    return IntegrityError("INSERT", {}, Exception("duplicate component"))


def test_create_component_returns_created_component(client, db_session):
    def populate_generated_fields(component):
        component.id = COMPONENT_ID
        component.created_at = CREATED_AT

    db_session.refresh.side_effect = populate_generated_fields

    response = client.post("/components", json=COMPONENT_PAYLOAD)

    assert response.status_code == 201
    assert response.json()["id"] == str(COMPONENT_ID)
    assert response.json()["part_number"] == "PN-1001"
    assert response.json()["status"] == "REGISTERED"
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()


def test_create_component_returns_conflict_for_duplicate(client, db_session):
    db_session.commit.side_effect = make_integrity_error()

    response = client.post("/components", json=COMPONENT_PAYLOAD)

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    db_session.rollback.assert_called_once()


def test_get_components_returns_component_list(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_component()]

    response = client.get("/components?skip=0&limit=100")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["serial_number"] == "SN-2026-001"


def test_get_component_returns_component(client, db_session):
    db_session.get.return_value = make_component()

    response = client.get(f"/components/{COMPONENT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(COMPONENT_ID)
    assert response.json()["component_type"] == "HYDRAULIC_PUMP"


def test_get_component_returns_404_when_missing(client, db_session):
    db_session.get.return_value = None

    response = client.get(f"/components/{COMPONENT_ID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Component not found"


def test_update_component_returns_updated_component(client, db_session):
    component = make_component()
    db_session.get.return_value = component
    update_payload = {
        **COMPONENT_PAYLOAD,
        "status": "UNDER_INSPECTION",
    }

    response = client.put(
        f"/components/{COMPONENT_ID}",
        json=update_payload,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "UNDER_INSPECTION"
    assert component.status == "UNDER_INSPECTION"
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(component)


def test_update_component_returns_404_when_missing(client, db_session):
    db_session.get.return_value = None

    response = client.put(
        f"/components/{COMPONENT_ID}",
        json=COMPONENT_PAYLOAD,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Component not found"


def test_update_component_returns_conflict_for_duplicate(client, db_session):
    db_session.get.return_value = make_component()
    db_session.commit.side_effect = make_integrity_error()

    response = client.put(
        f"/components/{COMPONENT_ID}",
        json=COMPONENT_PAYLOAD,
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]
    db_session.rollback.assert_called_once()


def test_get_db_closes_session(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    db_generator = database.get_db()

    assert next(db_generator) is session

    with pytest.raises(StopIteration):
        next(db_generator)

    session.close.assert_called_once()


def test_utc_now_returns_timezone_aware_utc_datetime():
    timestamp = utc_now()

    assert isinstance(timestamp, datetime)
    assert timestamp.tzinfo is UTC

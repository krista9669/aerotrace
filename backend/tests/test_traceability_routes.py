import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models import (
    Aircraft,
    Component,
    Engine,
    Installation,
    LifecycleEvent,
    Organisation,
)

AIRCRAFT_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789001")
ENGINE_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789002")
ENGINE_TWO_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789003")
COMPONENT_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789004")
INSTALLATION_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789005")
EVENT_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789006")
ORGANISATION_ID = uuid.UUID("71b6f280-4d5d-4fa5-9a29-123456789007")

CREATED_AT = datetime(2026, 11, 20, 10, 0, tzinfo=UTC)
INSTALLED_AT = datetime(2026, 11, 15, 8, 0, tzinfo=UTC)


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


def scalar_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


def make_aircraft():
    return Aircraft(
        id=AIRCRAFT_ID,
        registration="VT-XYZ",
        manufacturer="Airbus",
        model="A320neo",
        serial_number="AIR-2026-002",
        created_at=CREATED_AT,
    )


def make_engine(engine_id=ENGINE_ID, serial_number="ENG-2026-002"):
    return Engine(
        id=engine_id,
        serial_number=serial_number,
        manufacturer="CFM International",
        model="LEAP-1A",
        aircraft_id=AIRCRAFT_ID,
        created_at=CREATED_AT,
    )


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


def make_installation():
    return Installation(
        id=INSTALLATION_ID,
        component_id=COMPONENT_ID,
        engine_id=ENGINE_ID,
        installed_at=INSTALLED_AT,
        removed_at=None,
        installation_notes="Initial installation",
    )


def make_lifecycle_event():
    return LifecycleEvent(
        id=EVENT_ID,
        component_id=COMPONENT_ID,
        organisation_id=ORGANISATION_ID,
        event_type="INSPECTION",
        description="Routine component inspection",
        performed_by="Maintenance Technician",
        occurred_at=CREATED_AT,
        recorded_at=CREATED_AT,
    )


def make_organisation():
    return Organisation(
        id=ORGANISATION_ID,
        name="Aero Maintenance Services",
        organisation_type="MAINTENANCE",
        code="AMS001",
        created_at=CREATED_AT,
    )


def test_traceability_returns_404_when_aircraft_missing(client, db_session):
    db_session.get.return_value = None

    response = client.get(f"/aircraft/{AIRCRAFT_ID}/traceability")

    assert response.status_code == 404
    assert response.json()["detail"] == "Aircraft not found"
    db_session.scalars.assert_not_called()


def test_traceability_returns_empty_engines_when_aircraft_has_no_engines(
    client, db_session
):
    db_session.get.return_value = make_aircraft()
    db_session.scalars.return_value = scalar_result([])

    response = client.get(f"/aircraft/{AIRCRAFT_ID}/traceability")

    assert response.status_code == 200
    assert response.json()["aircraft"]["registration"] == "VT-XYZ"
    assert response.json()["engines"] == []
    db_session.scalars.assert_called_once()


def test_traceability_returns_engines_without_installations(client, db_session):
    aircraft = make_aircraft()
    engine = make_engine()

    db_session.get.return_value = aircraft
    db_session.scalars.side_effect = [
        scalar_result([engine]),
        scalar_result([]),
    ]

    response = client.get(f"/aircraft/{AIRCRAFT_ID}/traceability")

    assert response.status_code == 200
    assert len(response.json()["engines"]) == 1
    assert response.json()["engines"][0]["engine"]["serial_number"] == ("ENG-2026-002")
    assert response.json()["engines"][0]["installations"] == []


def test_traceability_returns_component_with_no_lifecycle_events(client, db_session):
    aircraft = make_aircraft()
    engine = make_engine()
    component = make_component()
    installation = make_installation()

    db_session.get.return_value = aircraft
    db_session.scalars.side_effect = [
        scalar_result([engine]),
        scalar_result([installation]),
        scalar_result([component]),
        scalar_result([]),
    ]

    response = client.get(f"/aircraft/{AIRCRAFT_ID}/traceability")

    assert response.status_code == 200

    component_data = response.json()["engines"][0]["installations"][0]["component"]

    assert component_data["component"]["serial_number"] == "SN-2026-001"
    assert component_data["lifecycle_events"] == []
    assert db_session.scalars.call_count == 4


def test_traceability_returns_complete_aircraft_history(client, db_session):
    aircraft = make_aircraft()
    engine_one = make_engine()
    engine_two = make_engine(
        engine_id=ENGINE_TWO_ID,
        serial_number="ENG-2026-003",
    )
    component = make_component()
    installation = make_installation()
    event = make_lifecycle_event()
    organisation = make_organisation()

    db_session.get.return_value = aircraft

    db_session.scalars.side_effect = [
        scalar_result([engine_one, engine_two]),
        scalar_result([installation]),
        scalar_result([component]),
        scalar_result([event]),
        scalar_result([organisation]),
    ]

    response = client.get(f"/aircraft/{AIRCRAFT_ID}/traceability")

    assert response.status_code == 200

    data = response.json()

    assert data["aircraft"]["id"] == str(AIRCRAFT_ID)
    assert data["aircraft"]["registration"] == "VT-XYZ"

    assert len(data["engines"]) == 2
    assert data["engines"][0]["engine"]["serial_number"] == "ENG-2026-002"

    assert len(data["engines"][0]["installations"]) == 1
    installation_data = data["engines"][0]["installations"][0]

    assert installation_data["installation"]["id"] == str(INSTALLATION_ID)
    assert installation_data["installation"]["removed_at"] is None

    component_data = installation_data["component"]

    assert component_data["component"]["serial_number"] == "SN-2026-001"
    assert component_data["component"]["status"] == "REGISTERED"

    assert len(component_data["lifecycle_events"]) == 1

    event_data = component_data["lifecycle_events"][0]

    assert event_data["event"]["event_type"] == "INSPECTION"
    assert event_data["organisation"]["name"] == "Aero Maintenance Services"

    assert data["engines"][1]["installations"] == []

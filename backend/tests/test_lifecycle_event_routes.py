import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.main import app
from app.models import Component, LifecycleEvent, Organisation

EVENT_ID = uuid.UUID("08b44a0c-4997-41bd-840a-3c9a602e08f8")
COMPONENT_ID = uuid.UUID("5487c281-4473-42b5-8fbf-4a1a3fac669c")
ORGANISATION_ID = uuid.UUID("5146c0bc-4c69-4d89-b677-3b40914be9b1")

OCCURRED_AT = datetime(2026, 11, 10, 3, 30, tzinfo=UTC)
RECORDED_AT = datetime(2026, 11, 9, 19, 0, tzinfo=UTC)

EVENT_PAYLOAD = {
    "component_id": str(COMPONENT_ID),
    "organisation_id": str(ORGANISATION_ID),
    "event_type": "INSPECTION",
    "description": "Routine inspection of hydraulic pump.",
    "performed_by": "Maintenance Technician",
    "occurred_at": "2026-11-10T09:00:00+05:30",
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
        status="UNDER_INSPECTION",
        created_at=RECORDED_AT,
    )


def make_organisation():
    return Organisation(
        id=ORGANISATION_ID,
        name="Aero Maintenance Services",
        organisation_type="MAINTENANCE",
        code="AMS001",
        created_at=RECORDED_AT,
    )


def make_event():
    return LifecycleEvent(
        id=EVENT_ID,
        component_id=COMPONENT_ID,
        organisation_id=ORGANISATION_ID,
        event_type="INSPECTION",
        description="Routine inspection of hydraulic pump.",
        performed_by="Maintenance Technician",
        occurred_at=OCCURRED_AT,
        recorded_at=RECORDED_AT,
    )


def make_integrity_error():
    return IntegrityError(
        "INSERT",
        {},
        Exception("database integrity error"),
    )


def test_create_lifecycle_event_returns_created_event(client, db_session):
    db_session.get.side_effect = [
        make_component(),
        make_organisation(),
    ]

    def populate_generated_fields(event):
        event.id = EVENT_ID
        event.recorded_at = RECORDED_AT

    db_session.refresh.side_effect = populate_generated_fields

    response = client.post(
        "/lifecycle-events",
        json=EVENT_PAYLOAD,
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(EVENT_ID)
    assert response.json()["event_type"] == "INSPECTION"
    assert response.json()["component_id"] == str(COMPONENT_ID)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once()


def test_create_event_returns_404_when_component_missing(client, db_session):
    db_session.get.return_value = None

    response = client.post(
        "/lifecycle-events",
        json=EVENT_PAYLOAD,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Component not found"
    db_session.add.assert_not_called()


def test_create_event_returns_404_when_organisation_missing(client, db_session):
    db_session.get.side_effect = [
        make_component(),
        None,
    ]

    response = client.post(
        "/lifecycle-events",
        json=EVENT_PAYLOAD,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Organisation not found"
    db_session.add.assert_not_called()


def test_create_event_returns_conflict_on_integrity_error(client, db_session):
    db_session.get.side_effect = [
        make_component(),
        make_organisation(),
    ]
    db_session.commit.side_effect = make_integrity_error()

    response = client.post(
        "/lifecycle-events",
        json=EVENT_PAYLOAD,
    )

    assert response.status_code == 409
    db_session.rollback.assert_called_once()


def test_create_event_rejects_naive_datetime(client, db_session):
    invalid_payload = {
        **EVENT_PAYLOAD,
        "occurred_at": "2026-11-10T09:00:00",
    }

    response = client.post(
        "/lifecycle-events",
        json=invalid_payload,
    )

    assert response.status_code == 422
    db_session.get.assert_not_called()


def test_get_lifecycle_events_returns_filtered_events(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_event()]

    response = client.get(
        "/lifecycle-events",
        params={
            "component_id": str(COMPONENT_ID),
            "organisation_id": str(ORGANISATION_ID),
            "event_type": "INSPECTION",
            "skip": 0,
            "limit": 100,
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(EVENT_ID)
    assert response.json()[0]["event_type"] == "INSPECTION"


def test_get_lifecycle_events_without_filters(client, db_session):
    db_session.scalars.return_value.all.return_value = [make_event()]

    response = client.get("/lifecycle-events")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_lifecycle_event_returns_event(client, db_session):
    db_session.get.return_value = make_event()

    response = client.get(f"/lifecycle-events/{EVENT_ID}")

    assert response.status_code == 200
    assert response.json()["id"] == str(EVENT_ID)
    assert response.json()["event_type"] == "INSPECTION"


def test_get_lifecycle_event_returns_404_when_missing(client, db_session):
    db_session.get.return_value = None

    response = client.get(f"/lifecycle-events/{EVENT_ID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Lifecycle event not found"

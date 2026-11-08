import uuid
from datetime import UTC, datetime

from sqlalchemy import UniqueConstraint

from app.core.database import Base
from app.models import (
    Aircraft,
    Component,
    Engine,
    Installation,
    LifecycleEvent,
    Organisation,
)


def test_all_models_are_registered():
    expected_tables = {
        "organisations",
        "aircraft",
        "engines",
        "components",
        "installations",
        "lifecycle_events",
    }

    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_organisation_model_fields():
    organisation = Organisation(
        name="Airline One",
        organisation_type="AIRLINE",
        code="AIR001",
    )

    assert organisation.name == "Airline One"
    assert organisation.organisation_type == "AIRLINE"
    assert organisation.code == "AIR001"


def test_aircraft_model_fields():
    aircraft = Aircraft(
        registration="VT-ABC",
        manufacturer="Airbus",
        model="A320",
        serial_number="AIR320001",
    )

    assert aircraft.registration == "VT-ABC"
    assert aircraft.manufacturer == "Airbus"
    assert aircraft.model == "A320"
    assert aircraft.serial_number == "AIR320001"


def test_engine_can_be_unassigned():
    engine = Engine(
        serial_number="ENG001",
        manufacturer="CFM",
        model="LEAP-1A",
    )

    assert engine.aircraft_id is None


def test_component_default_status():
    status_column = Component.__table__.columns["status"]

    assert status_column.default is not None
    assert status_column.default.arg == "REGISTERED"
    assert status_column.nullable is False


def test_component_identity_constraint():
    constraints = Component.__table__.constraints

    identity_constraint = next(
        constraint
        for constraint in constraints
        if isinstance(constraint, UniqueConstraint)
        and constraint.name == "uq_component_identity"
    )

    assert {column.name for column in identity_constraint.columns} == {
        "manufacturer",
        "part_number",
        "serial_number",
    }


def test_installation_nullable_fields():
    installed_at = datetime.now(UTC)

    installation = Installation(
        component_id=uuid.uuid4(),
        engine_id=uuid.uuid4(),
        installed_at=installed_at,
    )

    assert installation.installed_at == installed_at
    assert installation.removed_at is None
    assert installation.installation_notes is None


def test_lifecycle_event_fields():
    occurred_at = datetime.now(UTC)

    event = LifecycleEvent(
        component_id=uuid.uuid4(),
        organisation_id=uuid.uuid4(),
        event_type="INSPECTION",
        performed_by="Technician",
        occurred_at=occurred_at,
    )

    assert event.event_type == "INSPECTION"
    assert event.performed_by == "Technician"
    assert event.occurred_at == occurred_at
    assert event.description is None


def test_model_exports():
    from app import models

    expected_exports = {
        "Aircraft",
        "Component",
        "Engine",
        "Installation",
        "LifecycleEvent",
        "Organisation",
    }

    assert set(models.__all__) == expected_exports

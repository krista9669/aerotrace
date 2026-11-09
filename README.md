# AeroTrace
### Aircraft Component Lifecycle Tracking and Predictive Maintenance Platform

AeroTrace is an aviation technology platform for aircraft component lifecycle management and maintenance analytics. It combines a Python backend, a relational database, and a foundation for future machine learning and visualisation capabilities.

The current implementation includes a FastAPI backend, PostgreSQL persistence, a six-table lifecycle-domain schema, Alembic migrations, Docker Compose infrastructure, and REST APIs for component management, organisation management, and lifecycle-event recording and retrieval. Frontend development, installation workflows, and predictive maintenance capabilities remain planned work.

## 1. Project Objectives

- Maintain structured records of aircraft, engines, components, and organisations.
- Track component identity and current status.
- Record component lifecycle events and associate them with the relevant organisation.
- Establish a relational foundation for component installation, removal, maintenance, and transfers.
- Preserve data integrity through primary keys, foreign keys, uniqueness constraints, and versioned migrations.
- Prepare historical lifecycle data for future anomaly detection and predictive maintenance research.
- Provide an application interface and analytics visualisations as the platform evolves.

## 2. Implemented Functionality

### Component Management API

| Method | Endpoint | Description | Success response |
|---|---|---|---|
| `POST` | `/components` | Register a component | `201 Created` |
| `GET` | `/components` | List components with pagination | `200 OK` |
| `GET` | `/components/{component_id}` | Retrieve a component by UUID | `200 OK` |
| `PUT` | `/components/{component_id}` | Update a component's details and status | `200 OK` |

The list endpoint supports `skip` (default `0`, minimum `0`) and `limit` (default `100`, range `1–500`) query parameters.

Component identifiers are UUIDs. Component creation validates its request through Pydantic schemas and persists the record through SQLAlchemy. Retrieval and update operations return `404 Not Found` when the requested UUID does not exist. Component identity conflicts are returned as `409 Conflict` where a database uniqueness constraint is violated.

The update operation uses `PUT`, so clients must submit all editable component fields. Example request:

```json
{
  "part_number": "PN-1001",
  "serial_number": "SN-2026-001",
  "manufacturer": "Airbus",
  "component_type": "HYDRAULIC_PUMP",
  "status": "UNDER_INSPECTION"
}
```

### Organisation Management API

| Method | Endpoint | Description | Success response |
|---|---|---|---|
| `POST` | `/organisations` | Register an organisation | `201 Created` |
| `GET` | `/organisations` | List organisations with pagination | `200 OK` |

Organisation records include a name, organisation type, and unique organisation code. The list endpoint supports `skip` and `limit` pagination. A duplicate organisation code returns `409 Conflict`.

Example creation request:

```json
{
  "name": "Aero Maintenance Services",
  "organisation_type": "MAINTENANCE",
  "code": "AMS001"
}
```

### Lifecycle Event API

| Method | Endpoint | Description | Success response |
|---|---|---|---|
| `POST` | `/lifecycle-events` | Record a lifecycle event for a component | `201 Created` |
| `GET` | `/lifecycle-events` | List lifecycle events with optional filters and pagination | `200 OK` |
| `GET` | `/lifecycle-events/{event_id}` | Retrieve a lifecycle event by UUID | `200 OK` |

A lifecycle event is associated with both a component and an organisation. Event records include an event type, optional description, performer, occurrence timestamp, and database-generated recording timestamp.

The create endpoint verifies that the referenced component and organisation exist before inserting the event. Missing references return `404 Not Found`; database integrity conflicts return `409 Conflict`. The `occurred_at` field must include a timezone. The API stores and returns the corresponding timestamp, normalised by the database/session configuration as applicable.

The list endpoint supports optional filters:

- `component_id`
- `organisation_id`
- `event_type`
- `skip` and `limit` pagination parameters

Results are ordered by occurrence time in descending order, with recording time used as a secondary descending sort. The individual retrieval endpoint returns `404 Not Found` when the event UUID does not exist.

Example creation request (replace the UUIDs with existing records in your database):

```json
{
  "component_id": "00000000-0000-0000-0000-000000000001",
  "organisation_id": "00000000-0000-0000-0000-000000000002",
  "event_type": "INSPECTION",
  "description": "Routine inspection of hydraulic pump.",
  "performed_by": "Maintenance Technician",
  "occurred_at": "2026-11-10T09:00:00+05:30"
}
```

Lifecycle events currently support creation and retrieval. Update and deletion endpoints have not been implemented.

### Health Check

| Method | Endpoint | Description | Success response |
|---|---|---|---|
| `GET` | `/health` | Check API service health | `200 OK` |

### Database and Lifecycle Schema

The initial Alembic migration creates six core tables:

| Table | Purpose |
|---|---|
| `aircraft` | Aircraft registration, manufacturer, model, and serial number |
| `engines` | Engine identity and optional association with an aircraft |
| `components` | Component part number, serial number, manufacturer, type, and status |
| `organisations` | Organisation identity, type, and unique code |
| `lifecycle_events` | Component events, associated organisation, performer, and timestamps |
| `installations` | Component-to-engine installation and removal records |

The schema uses UUID primary keys, foreign-key relationships, timestamp fields, and uniqueness constraints for key identifiers. The component identity constraint is defined over manufacturer, part number, and serial number. Alembic manages schema versioning and migration execution.

The organisation and lifecycle-event APIs use the existing `organisations` and `lifecycle_events` tables created by the initial migration; no additional schema migration was required for these API additions.

### Backend and Configuration

- FastAPI application with interactive OpenAPI documentation.
- Pydantic request and response schemas.
- Pydantic Settings for environment-based configuration.
- SQLAlchemy ORM and a reusable database-session dependency.
- Psycopg PostgreSQL driver.
- Separate routers for components, organisations, and lifecycle events.

### Containerised Development

- PostgreSQL 16 runs as a Docker Compose service with a persistent named volume.
- The FastAPI backend is built from `backend/Dockerfile`.
- The backend waits for the PostgreSQL health check before starting.
- The database connection string is supplied to the backend through environment variables.

### Quality and Automation

The repository contains GitHub Actions workflows for:

- **Backend CI:** dependency installation, backend import validation, Ruff linting and formatting checks, automated tests with a coverage threshold, and database migration validation against a fresh CI PostgreSQL database.
- **Docker Build CI:** building the backend Docker image as a CI validation step.
- **CodeQL Advanced:** automated code scanning for Python and GitHub Actions workflows.

The current local backend test run reports **33 passing tests and 100% total application coverage**. Workflow files are configured in the repository. Check the GitHub Actions tab for the latest execution results; workflow configuration alone does not guarantee that the latest run passed.

## 3. Planned System Modules

### Component Lifecycle Management

- Installation and removal workflows.
- Maintenance and inspection record management beyond the current lifecycle-event API foundation.
- Component transfer tracking.
- Historical lifecycle reconstruction and querying enhancements.

### Machine Learning and Analytics

- Lifecycle data extraction, preprocessing, and feature engineering.
- Anomaly detection in historical component records.
- Predictive maintenance modelling.
- Component risk assessment and model evaluation.
- Model inference integration with backend APIs.

### Full-Stack Application

- React and TypeScript component management interface.
- Aircraft and component views.
- Maintenance analytics dashboard.
- Lifecycle history visualisation.
- Reporting and user-facing analytics.

These are planned capabilities and should not be interpreted as implemented functionality.

## 4. Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Backend | Python, FastAPI | Implemented |
| Request/response validation | Pydantic | Implemented |
| Database | PostgreSQL 16 | Configured |
| ORM | SQLAlchemy | Implemented |
| Database migrations | Alembic | Initial migration created |
| Database driver | Psycopg | Configured |
| Containerisation | Docker, Docker Compose | Configured |
| API documentation | OpenAPI / Swagger UI | Available through FastAPI |
| Frontend | React, TypeScript | Planned |
| Data processing and ML | Pandas, NumPy, Scikit-learn | Planned |

## 5. Architecture

AeroTrace is documented at two levels: the current deployment architecture, which shows the running infrastructure, and the target application architecture, which shows how planned user-interface and domain-service modules will connect to the backend and database.

### Current Deployment Architecture

```mermaid
flowchart TB
    Client["Browser / API client"]
    subgraph Host["Developer machine / Docker host"]
        subgraph Compose["Docker Compose environment"]
            API["AeroTrace API<br/>FastAPI backend container<br/>Port 8000"]
            DB[("PostgreSQL 16<br/>Database container<br/>Port 5432")]
            Volume[("Persistent named volume<br/>aerotrace_pgdata")]
            Migration["Alembic migration tooling<br/>alembic upgrade head"]
            API -->|"SQLAlchemy + Psycopg"| DB
            Migration -->|"Apply schema revisions"| DB
            DB ---|"Persistent database files"| Volume
        end
        Client -->|"HTTP / REST"| API
    end
```

### Target Application Architecture

The frontend, installation workflows, machine-learning services, and analytics views below are planned integrations. Component, organisation, and lifecycle-event API foundations are implemented in the backend.

```mermaid
flowchart TB
    User["User / Maintenance analyst"]
    UI["Frontend application<br/>React + TypeScript<br/>(planned)"]
    API["FastAPI REST API<br/>Components · Organisations · Lifecycle Events"]
    subgraph Services["Application services"]
        Components["Component management<br/>Registration · Listing · Retrieval · Update"]
        Organisations["Organisation management<br/>Registration · Listing"]
        Lifecycle["Lifecycle event management<br/>Creation · Filtering · Retrieval"]
        Future["Future services<br/>Installation workflows · Predictive maintenance<br/>(planned)"]
    end
    ORM["SQLAlchemy persistence layer"]
    DB[("PostgreSQL 16")]
    User --> UI
    UI -.->|"REST / JSON"| API
    API --> Components
    API --> Organisations
    API --> Lifecycle
    API -.-> Future
    Components --> ORM
    Organisations --> ORM
    Lifecycle --> ORM
    Future -.-> ORM
    ORM --> DB
```

## 6. Repository Structure

```text
aerotrace/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       ├── codeql.yml
│       └── docker-ci.yml
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── components.py
│   │   │       ├── organisations.py
│   │   │       └── lifecycle_events.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── entities.py
│   │   ├── schemas/
│   │   │   ├── component.py
│   │   │   ├── organisation.py
│   │   │   └── lifecycle_event.py
│   │   └── main.py
│   ├── migrations/
│   │   ├── versions/
│   │   │   └── 78282062446d_create_initial_core_tables.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── test_component_routes.py
│   │   ├── test_lifecycle_event_routes.py
│   │   ├── test_organisation_routes.py
│   │   ├── test_main.py
│   │   └── test_models.py
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── requirements.txt
│   └── requirements-dev.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## 7. Getting Started

### Prerequisites

- Git
- Docker Desktop with Docker Compose, or a local Python 3.12+ environment
- PostgreSQL 16 if you are not using the supplied Docker Compose database

### Clone the Repository

```bash
git clone https://github.com/krista9669/aerotrace.git
cd aerotrace
```

### Configure Environment Variables

For Docker Compose, create a root `.env` file using `.env.example` as a starting point:

```env
POSTGRES_DB=aerotrace
POSTGRES_USER=aerotrace
POSTGRES_PASSWORD=change_me
```

Replace the example password with a strong local development password. Keep real `.env` files out of version control; do not commit passwords or other secrets.

For direct local backend execution, create `backend/.env` with a connection string for your PostgreSQL instance:

```env
DATABASE_URL=postgresql+psycopg://aerotrace:your_password@localhost:5432/aerotrace
```

Use the actual username, password, host, and database configured in your environment. The local connection string must match the PostgreSQL credentials. When running the backend in Docker Compose, Compose supplies `DATABASE_URL` to the container using the `postgres` service hostname.

### Start the Application with Docker Compose

From the repository root:

```bash
docker compose up --build -d
```

Check service status:

```bash
docker compose ps
```

The backend is available at `http://127.0.0.1:8000`, and PostgreSQL is exposed on port `5432`.

### Apply Database Migrations

Run the schema migration inside the backend container:

```bash
docker compose exec backend alembic upgrade head
```

Inspect the current migration revision:

```bash
docker compose exec backend alembic current
```

Check whether SQLAlchemy metadata and the migrated database schema differ:

```bash
docker compose exec backend alembic check
```

### Run the Backend Locally (Without the Backend Container)

Start PostgreSQL separately, then create a virtual environment:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Set `DATABASE_URL` in `backend/.env`, apply migrations, and start the development server:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Do not start a second backend on port `8000` while the Docker backend is already using that port.

### API Documentation

| Resource | URL |
|---|---|
| Interactive API documentation | http://127.0.0.1:8000/docs |
| OpenAPI schema | http://127.0.0.1:8000/openapi.json |
| Health check | http://127.0.0.1:8000/health |

The Swagger UI groups the endpoints by router and can be used to exercise the component, organisation, and lifecycle-event operations.

## 8. Testing and Code Quality

From the `backend` directory, install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the automated tests under the `tests` directory with coverage enforcement:

```bash
python -m pytest tests --cov=app --cov-report=term-missing --cov-fail-under=90
```

The local test run currently reports 33 passing tests and 100% total application coverage. The command deliberately targets `tests/` and does not collect the separate `backend/test_db.py` database-connection smoke script. That script uses the local `DATABASE_URL` and should only be run when its credentials match your PostgreSQL configuration. The GitHub Actions workflow provides its own test database credentials.

Run linting and formatting checks from the `backend` directory:

```bash
ruff check .
ruff format --check .
```

The Backend CI workflow also validates migrations against a fresh CI PostgreSQL database. Check GitHub Actions for the latest workflow results.

## 9. Development Roadmap

### Backend and Database

- [x] Initial FastAPI backend setup.
- [x] Environment-based application configuration.
- [x] SQLAlchemy database foundation and database-session dependency.
- [x] PostgreSQL 16 Docker Compose service with persistent storage.
- [x] Backend Dockerfile and container orchestration.
- [x] Initial relational schema for aircraft, engines, components, organisations, lifecycle events, and installations.
- [x] Alembic migration for the initial core tables.
- [x] Component registration, listing, retrieval, and update APIs.
- [x] Organisation registration and listing APIs.
- [x] Lifecycle-event creation, filtered listing, and individual retrieval APIs.
- [x] Automated route tests for components, organisations, and lifecycle events.
- [x] Local backend test run: 33 tests passed with 100% total application coverage.
- [x] Backend CI, Docker build CI, and CodeQL workflows configured.
- [ ] Component deletion API (subject to lifecycle-data integrity requirements).
- [ ] Installation and removal workflows.
- [ ] Authentication, authorisation, and audit controls.
- [ ] Query optimisation and expanded integration testing.

### Frontend

- [ ] React and TypeScript application.
- [ ] Component and aircraft management screens.
- [ ] Organisation management screens.
- [ ] Lifecycle history interface.
- [ ] Maintenance analytics dashboard.
- [ ] Data visualisation and reporting.

### Machine Learning and Analytics

- [ ] Historical lifecycle dataset preparation.
- [ ] Feature engineering and exploratory analysis.
- [ ] Anomaly detection baseline.
- [ ] Predictive maintenance model development.
- [ ] Model evaluation and risk analysis.
- [ ] Model inference integration with backend APIs.

### Delivery

- [ ] End-to-end application testing.
- [ ] Deployment configuration and operational monitoring.
- [ ] API usage and system operation documentation.

## 10. Project Scope and Safety

AeroTrace is an experimental aviation technology platform focused on software engineering, database management, and machine learning applications in aircraft component lifecycle analysis.

Machine learning outputs are intended for analytical and research purposes only. They are not substitutes for certified aviation maintenance procedures, approved maintenance data, or regulatory assessments. The platform is not intended to make airworthiness decisions.

## 11. Project Information

| Attribute | Details |
|---|---|
| Project Name | AeroTrace |
| Domain | Aviation Technology |
| Project Type | Full-Stack Application (in development) |
| Core Areas | Component Lifecycle Management, Database Engineering, Machine Learning, Web Development |
| Backend | Python, FastAPI |
| Database | PostgreSQL 16 |
| ORM and Migrations | SQLAlchemy, Alembic |
| Containerisation | Docker, Docker Compose |
| Frontend | React, TypeScript (planned) |
| Machine Learning | Pandas, NumPy, Scikit-learn (planned) |
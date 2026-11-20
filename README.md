# AeroTrace
### Aircraft Component Lifecycle Tracking and Predictive Maintenance Platform

AeroTrace is an aviation technology platform for aircraft component lifecycle management and maintenance analytics. It combines a Python backend, PostgreSQL, and a foundation for future machine-learning and visualisation capabilities.

The current implementation includes a FastAPI backend, a six-table lifecycle-domain schema, Alembic migrations, Docker Compose infrastructure, and REST APIs for aircraft, engines, components, organisations, lifecycle events, component installations/removals, and aircraft-level traceability. The backend preserves installation history and can assemble an aircraft's associated engine, component, installation, and lifecycle-event records into one nested response. Frontend development and predictive-maintenance capabilities remain planned work.

## 1. Project Objectives

- Maintain structured records of aircraft, engines, components, and organisations.
- Associate engines with aircraft while allowing unassigned engines.
- Track component identity, status, installation, removal, and installation history.
- Record component lifecycle events and the organisations responsible for them.
- Retrieve aircraft-level traceability across engines, installations, components, and recorded events.
- Preserve data integrity using primary keys, foreign keys, uniqueness constraints, and versioned migrations.
- Prepare lifecycle data for future anomaly detection and predictive-maintenance research.

## 2. Implemented Functionality

### Aircraft Management API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/aircraft` | Register an aircraft | `201 Created` |
| `GET` | `/aircraft` | List aircraft with pagination | `200 OK` |
| `GET` | `/aircraft/{aircraft_id}` | Retrieve an aircraft by UUID | `200 OK` |

Aircraft records include registration, manufacturer, model, serial number, and a database-generated creation timestamp. Registration and serial number are unique. Duplicate values return `409 Conflict`; a missing aircraft UUID returns `404 Not Found`. The list endpoint supports `skip` (default `0`, minimum `0`) and `limit` (default `100`, range `1–500`).

Example request:

```json
{
  "registration": "VT-XYZ",
  "manufacturer": "Airbus",
  "model": "A320neo",
  "serial_number": "AIR-2026-002"
}
```

### Engine Management API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/engines` | Register an engine | `201 Created` |
| `GET` | `/engines` | List engines with pagination | `200 OK` |
| `GET` | `/engines/{engine_id}` | Retrieve an engine by UUID | `200 OK` |

An engine contains a serial number, manufacturer, model, and optional `aircraft_id`. When an aircraft ID is supplied, the API verifies that the aircraft exists. Duplicate engine serial numbers return `409 Conflict`; a missing referenced aircraft returns `404 Not Found`.

Example request with an aircraft association (use an existing aircraft UUID):

```json
{
  "serial_number": "ENG-2026-002",
  "manufacturer": "CFM International",
  "model": "LEAP-1A",
  "aircraft_id": "303fe6bc-68b2-4227-8c7c-d40cd5e904f5"
}
```

### Component Management API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/components` | Register a component | `201 Created` |
| `GET` | `/components` | List components with pagination | `200 OK` |
| `GET` | `/components/{component_id}` | Retrieve a component by UUID | `200 OK` |
| `PUT` | `/components/{component_id}` | Update component details and status | `200 OK` |

Component identity is constrained by manufacturer, part number, and serial number. Missing component IDs return `404 Not Found`; duplicate component identity returns `409 Conflict`. The list endpoint supports `skip` and `limit` pagination. The update operation uses `PUT`, so clients submit all editable fields.

Example request:

```json
{
  "part_number": "PN-1001",
  "serial_number": "SN-2026-001",
  "manufacturer": "Airbus",
  "component_type": "HYDRAULIC_PUMP",
  "status": "REGISTERED"
}
```

### Organisation Management API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/organisations` | Register an organisation | `201 Created` |
| `GET` | `/organisations` | List organisations with pagination | `200 OK` |

Organisation records contain a name, organisation type, and unique organisation code. Duplicate codes return `409 Conflict`.

Example request:

```json
{
  "name": "Aero Maintenance Services",
  "organisation_type": "MAINTENANCE",
  "code": "AMS001"
}
```

### Lifecycle Event API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/lifecycle-events` | Record a lifecycle event for a component | `201 Created` |
| `GET` | `/lifecycle-events` | List events with optional filters and pagination | `200 OK` |
| `GET` | `/lifecycle-events/{event_id}` | Retrieve an event by UUID | `200 OK` |

Each lifecycle event is associated with a component and an organisation. It includes an event type, optional description, performer, occurrence timestamp, and database-generated recording timestamp. The API verifies that the component and organisation exist. Missing references return `404 Not Found`; integrity conflicts return `409 Conflict`. `occurred_at` must include a timezone.

The list endpoint supports optional `component_id`, `organisation_id`, and `event_type` filters plus `skip` and `limit`. Results are ordered by occurrence time and recording time, both descending. Lifecycle events currently support creation and retrieval; update and delete endpoints are not implemented.

Example request (replace the UUIDs with existing records):

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

### Component Installation and Removal API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/installations` | Install a component on an engine | `201 Created` |
| `GET` | `/installations` | List installation history with optional filters and pagination | `200 OK` |
| `GET` | `/installations/{installation_id}` | Retrieve an installation record | `200 OK` |
| `POST` | `/installations/{installation_id}/remove` | Record component removal | `200 OK` |

An installation associates a component with an engine and stores timezone-aware `installed_at`, nullable `removed_at` (null means active), and optional `installation_notes`.

The workflow requires the component and engine to exist, and the component to have `REGISTERED` status. A component cannot have more than one active installation. Installation changes component status to `INSTALLED`. Removal records a timestamp later than `installed_at`, changes component status back to `REGISTERED`, and updates the existing installation record rather than deleting it. If `removed_at` is omitted, the API uses current UTC time. Missing records return `404 Not Found`; invalid states and conflicts return `409 Conflict`; invalid timestamp ordering returns `422 Unprocessable Entity`.

The list endpoint supports `component_id`, `engine_id`, `skip`, and `limit` filters. Results are ordered by installation time descending.

Example installation request (replace IDs with existing records):

```json
{
  "component_id": "00000000-0000-0000-0000-000000000001",
  "engine_id": "00000000-0000-0000-0000-000000000002",
  "installed_at": "2026-11-15T08:30:00+05:30",
  "installation_notes": "Initial installation during maintenance."
}
```

Example removal request using the current UTC time:

```json
{}
```

### Aircraft Component Traceability API

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `GET` | `/aircraft/{aircraft_id}/traceability` | Retrieve an aircraft with associated engines, installation history, components, lifecycle events, and event organisations | `200 OK` |

This read-only endpoint assembles existing relational records into a single nested response. It does not modify data and requires no database migration.

The response hierarchy is:

1. **Aircraft:** the aircraft identified by `aircraft_id`.
2. **Engines:** engines whose `aircraft_id` references that aircraft.
3. **Installations:** installation records associated with those engines, including active and removed installations.
4. **Components:** component details for each installation.
5. **Lifecycle events:** events associated with each referenced component, ordered by occurrence and recording time descending.
6. **Organisations:** the organisation associated with each lifecycle event.

A missing aircraft returns `404 Not Found`. An aircraft without engines returns an empty `engines` array. Engines without installations return an empty `installations` array; components without lifecycle events return an empty `lifecycle_events` array.

Example request:

```http
GET /aircraft/303fe6bc-68b2-4227-8c7c-d40cd5e904f5/traceability
```

The response uses this general structure (values are illustrative):

```json
{
  "aircraft": {
    "id": "303fe6bc-68b2-4227-8c7c-d40cd5e904f5",
    "registration": "VT-XYZ",
    "manufacturer": "Airbus",
    "model": "A320neo",
    "serial_number": "AIR-2026-002",
    "created_at": "2026-11-19T16:21:43.576168Z"
  },
  "engines": [
    {
      "engine": {
        "id": "87412221-eb54-4ca7-b87b-915aec995f30",
        "serial_number": "ENG-2026-002",
        "manufacturer": "CFM International",
        "model": "LEAP-1A",
        "aircraft_id": "303fe6bc-68b2-4227-8c7c-d40cd5e904f5",
        "created_at": "2026-11-19T16:26:58.329308Z"
      },
      "installations": [
        {
          "installation": {
            "id": "9c02763d-84cd-40ca-a57d-de1470d539bd",
            "component_id": "5487c281-4473-42b5-8fbf-4a1a3fac669c",
            "engine_id": "87412221-eb54-4ca7-b87b-915aec995f30",
            "installed_at": "2026-11-20T03:30:00Z",
            "removed_at": null,
            "installation_notes": "Installed on aircraft VT-XYZ for traceability verification"
          },
          "component": {
            "component": {
              "id": "5487c281-4473-42b5-8fbf-4a1a3fac669c",
              "part_number": "PN-1001",
              "serial_number": "SN-2026-001",
              "manufacturer": "Airbus",
              "component_type": "HYDRAULIC_PUMP",
              "status": "INSTALLED",
              "created_at": "2026-11-09T07:30:17.426375Z"
            },
            "lifecycle_events": [
              {
                "event": {
                  "id": "08b44a0c-4997-41bd-840a-3c9a602e08f8",
                  "component_id": "5487c281-4473-42b5-8fbf-4a1a3fac669c",
                  "organisation_id": "5146c0bc-4c69-4d89-b677-3b40914be9b1",
                  "event_type": "INSPECTION",
                  "description": "Routine inspection of hydraulic pump.",
                  "performed_by": "Maintenance Technician",
                  "occurred_at": "2026-11-10T03:30:00Z",
                  "recorded_at": "2026-11-09T19:00:00.245777Z"
                },
                "organisation": {
                  "id": "5146c0bc-4c69-4d89-b677-3b40914be9b1",
                  "name": "Aero Maintenance Services",
                  "organisation_type": "MAINTENANCE",
                  "code": "AMS001",
                  "created_at": "2026-11-09T18:56:44.841052Z"
                }
              }
            ]
          }
        }
      ]
    }
  ]
}
```

The endpoint returns installation records for engines associated with the requested aircraft. Lifecycle events are associated with components, so the events shown represent the recorded component history, not a timeline filtered to one installation's date range.

### Health Check

| Method | Endpoint | Description | Success |
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

The schema uses UUID primary keys, foreign-key relationships, timestamp fields, and uniqueness constraints. Component identity is unique over manufacturer, part number, and serial number. Alembic manages schema versioning. The traceability endpoint reads from existing tables and introduces no additional table or migration.

### Backend and Configuration

- FastAPI application with interactive OpenAPI documentation.
- Pydantic request and response schemas, including nested traceability response schemas.
- Pydantic Settings for environment-based configuration.
- SQLAlchemy ORM and a reusable database-session dependency.
- Psycopg PostgreSQL driver.
- Separate routers for aircraft, components, engines, organisations, lifecycle events, installations, and traceability.

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

The latest local test run for the traceability implementation reports **73 passing tests and 100% total application coverage (568 statements, zero missed)**. The five dedicated traceability tests cover missing aircraft, empty aircraft/engine relationships, and complete nested history. Run Ruff linting and formatting checks before committing. Check GitHub Actions for the latest remote workflow results; workflow configuration alone does not guarantee that the latest run passed.

## 3. Planned System Modules

### Component Lifecycle Management

- Maintenance and inspection record management enhancements.
- Component transfer tracking.
- Historical lifecycle reconstruction and querying enhancements.
- Additional controls and validation for complex installation histories.

### Machine Learning and Analytics

- Lifecycle data extraction, preprocessing, and feature engineering.
- Anomaly detection in historical component records.
- Predictive maintenance modelling.
- Component risk assessment and model evaluation.
- Model inference integration with backend APIs.

### Full-Stack Application

- React and TypeScript component management interface.
- Aircraft, engine, and component views.
- Organisation management screens.
- Maintenance analytics dashboard.
- Lifecycle and installation history visualisation.
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

The current deployment architecture shows the running infrastructure. The backend domain architecture shows implemented API groups and their persistence layer. The frontend and predictive-maintenance modules remain planned integrations.

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

### Current Backend Domain Architecture

```mermaid
flowchart TB
    Client["Swagger UI / API client"] --> API["FastAPI application"]
    subgraph Routers["Implemented API routers"]
        Aircraft["Aircraft"]
        Components["Components"]
        Engines["Engines"]
        Organisations["Organisations"]
        Events["Lifecycle events"]
        Installations["Installations and removals"]
        Traceability["Aircraft traceability"]
    end
    API --> Aircraft
    API --> Components
    API --> Engines
    API --> Organisations
    API --> Events
    API --> Installations
    API --> Traceability
    Aircraft --> ORM["SQLAlchemy persistence layer"]
    Components --> ORM
    Engines --> ORM
    Organisations --> ORM
    Events --> ORM
    Installations --> ORM
    Traceability --> ORM
    ORM --> DB[("PostgreSQL 16")]
```

### Aircraft Component Traceability Flow

```mermaid
flowchart TB
    Aircraft["Aircraft"] --> Engines["Associated engines"]
    Engines --> Installations["Installation history"]
    Installations --> Components["Components"]
    Components --> Events["Lifecycle events"]
    Events --> Organisations["Performing organisations"]
```

### Target Application Architecture

The frontend, machine-learning services, and analytics views below are planned integrations.

```mermaid
flowchart TB
    User["User / Maintenance analyst"]
    UI["Frontend application<br/>React + TypeScript<br/>(planned)"]
    API["FastAPI REST API<br/>Aircraft · Engines · Components<br/>Organisations · Events · Installations · Traceability"]
    subgraph Services["Future application services — planned"]
        ML["Machine learning and analytics<br/>Preprocessing · Anomaly detection · Prediction"]
        Reports["Analytics and visualisation<br/>Dashboards · Reports · Risk analysis"]
    end
    ORM["SQLAlchemy persistence layer"]
    DB[("PostgreSQL 16")]
    User --> UI
    UI -.->|"REST / JSON"| API
    API --> ORM
    ORM --> DB
    DB -.-> ML
    ML -.-> Reports
    DB -.-> Reports
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
│   │   │       ├── aircraft.py
│   │   │       ├── components.py
│   │   │       ├── engines.py
│   │   │       ├── installations.py
│   │   │       ├── lifecycle_events.py
│   │   │       ├── organisations.py
│   │   │       └── traceability.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── entities.py
│   │   ├── schemas/
│   │   │   ├── aircraft.py
│   │   │   ├── component.py
│   │   │   ├── engine.py
│   │   │   ├── installation.py
│   │   │   ├── lifecycle_event.py
│   │   │   ├── organisation.py
│   │   │   └── traceability.py
│   │   └── main.py
│   ├── migrations/
│   │   ├── versions/
│   │   │   └── 78282062446d_create_initial_core_tables.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── test_aircraft_routes.py
│   │   ├── test_component_routes.py
│   │   ├── test_engine_routes.py
│   │   ├── test_installation_routes.py
│   │   ├── test_lifecycle_event_routes.py
│   │   ├── test_organisation_routes.py
│   │   ├── test_traceability_routes.py
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

Use the actual username, password, host, and database configured in your environment. When running the backend in Docker Compose, Compose supplies `DATABASE_URL` to the container using the `postgres` service hostname.

### Start the Application with Docker Compose

From the repository root:

```bash
docker compose up --build -d
docker compose ps
```

The backend is available at `http://127.0.0.1:8000`, and PostgreSQL is exposed on port `5432`.

### Apply Database Migrations

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
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

Install development dependencies, set `DATABASE_URL` in `backend/.env`, apply migrations, and start the development server:

```bash
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run backend commands such as `uvicorn`, `pytest`, and Ruff from the `backend` directory. Do not start a second backend on port `8000` while the Docker backend is already using that port. When source files change and the Docker backend is in use, rebuild only that service:

```bash
docker compose build backend
docker compose up -d --no-deps backend
```

This leaves the PostgreSQL service and its persistent volume in place.

### API Documentation

| Resource | URL |
|---|---|
| Interactive API documentation | http://127.0.0.1:8000/docs |
| OpenAPI schema | http://127.0.0.1:8000/openapi.json |
| Health check | http://127.0.0.1:8000/health |

Swagger UI groups operations by router and can be used to exercise the implemented APIs.

## 8. Testing and Code Quality

Run automated tests from the `backend` directory:

```bash
python -m pytest tests --cov=app --cov-report=term-missing --cov-fail-under=90
```

The latest local run for the traceability implementation reports **73 passing tests and 100% total application coverage (568 statements, zero missed)**. The command targets `tests/` and does not collect the separate `backend/test_db.py` database-connection smoke script. That script uses the local `DATABASE_URL` and should only be run when its credentials match the PostgreSQL configuration.

Run linting and formatting checks from the `backend` directory:

```bash
ruff check .
ruff format --check .
```

The Backend CI workflow also validates migrations against a fresh CI PostgreSQL database. Check GitHub Actions for the latest remote workflow results.

## 9. Development Roadmap

### Backend and Database

- [x] Initial FastAPI backend setup and environment-based configuration.
- [x] SQLAlchemy database foundation and reusable database-session dependency.
- [x] PostgreSQL 16 Docker Compose service with persistent storage.
- [x] Backend Dockerfile and container orchestration.
- [x] Initial relational schema and Alembic migration for aircraft, engines, components, organisations, lifecycle events, and installations.
- [x] Aircraft registration, listing, and retrieval APIs.
- [x] Engine registration, listing, and retrieval APIs, including optional aircraft association.
- [x] Component registration, listing, retrieval, and update APIs.
- [x] Organisation registration and listing APIs.
- [x] Lifecycle-event creation, filtered listing, and retrieval APIs.
- [x] Component installation, installation history, and removal APIs.
- [x] Component status transitions on installation and removal.
- [x] Aircraft-level component traceability endpoint and nested response schemas.
- [x] Automated route tests for the implemented API groups.
- [x] Local backend test run: 73 tests passed with 100% total application coverage.
- [x] Aircraft, engine, installation, and lifecycle traceability verified against the running Docker/PostgreSQL environment.
- [x] Backend CI, Docker Build CI, and CodeQL workflows configured.
- [ ] Authentication, authorisation, and audit controls.
- [ ] Expanded integration and concurrency testing against PostgreSQL.
- [ ] Query optimisation and operational monitoring.

### Frontend

- [ ] React and TypeScript application.
- [ ] Aircraft, engine, and component management screens.
- [ ] Organisation management screens.
- [ ] Installation and removal workflow interface.
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

AeroTrace is an experimental aviation technology platform focused on software engineering, database management, and machine-learning applications in aircraft component lifecycle analysis.

Machine-learning outputs are intended for analytical and research purposes only. They are not substitutes for certified aviation maintenance procedures, approved maintenance data, or regulatory assessments. The platform is not intended to make airworthiness decisions.

## 11. Project Information

| Attribute | Details |
|---|---|
| Project Name | AeroTrace |
| Domain | Aviation Technology |
| Project Type | Full-Stack Application (in development) |
| Core Areas | Aircraft and Component Lifecycle Management, Database Engineering, Machine Learning, Web Development |
| Backend | Python, FastAPI |
| Database | PostgreSQL 16 |
| ORM and Migrations | SQLAlchemy, Alembic |
| Containerisation | Docker, Docker Compose |
| Frontend | React, TypeScript (planned) |
| Machine Learning | Pandas, NumPy, Scikit-learn (planned) |
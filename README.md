# AeroTrace
### Aircraft Component Lifecycle Tracking and Predictive Maintenance Platform

AeroTrace is an aviation technology platform for aircraft component lifecycle management and maintenance analytics. It combines a Python backend, a relational database, and a foundation for future machine learning and visualisation capabilities.

The current implementation establishes the backend service, PostgreSQL persistence infrastructure, initial lifecycle-domain schema, containerised development environment, database migrations, and automated quality checks. Component management APIs, the frontend, and predictive models are planned development areas.

## 1. Project Objectives

- Maintain structured records of aircraft, engines, components, and organisations.
- Establish a traceable foundation for component installation and lifecycle events.
- Store lifecycle information in a relational PostgreSQL database.
- Preserve data integrity through primary keys, foreign keys, uniqueness constraints, and versioned migrations.
- Prepare historical lifecycle data for future anomaly detection and predictive maintenance research.
- Provide an application interface and analytics visualisations as the platform evolves.

## 2. Current Implementation

### Backend API

- FastAPI application with service metadata and a health-check endpoint.
- Environment-based configuration using Pydantic Settings.
- SQLAlchemy database engine and declarative model foundation.
- Interactive API documentation through FastAPI's OpenAPI interface.

The health endpoint is currently the implemented API route; component and lifecycle CRUD endpoints remain on the roadmap.

### Database and Lifecycle Schema

The initial Alembic migration creates six core tables:

| Table | Purpose |
|---|---|
| `aircraft` | Aircraft registration, manufacturer, model, and serial number |
| `engines` | Engine identity and optional association with an aircraft |
| `components` | Component part number, serial number, manufacturer, type, and status |
| `organisations` | Organisation identity, type, and code |
| `lifecycle_events` | Component events, associated organisation, performer, and timestamps |
| `installations` | Component-to-engine installation and removal records |

The schema uses UUID primary keys, foreign-key relationships, timestamp fields, and uniqueness constraints for key identifiers. Alembic manages schema versioning and migration execution.

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

These workflows are configured in the repository. Their latest execution status should be checked in the GitHub Actions tab.

## 3. Planned System Modules

### Component Lifecycle Management

- Component registration and identification APIs.
- Installation and removal workflows.
- Maintenance and inspection record management.
- Component transfer tracking.
- Historical lifecycle reconstruction and querying.

### Machine Learning and Analytics

- Lifecycle data extraction, preprocessing, and feature engineering.
- Anomaly detection in historical component records.
- Predictive maintenance modelling.
- Component risk assessment and model evaluation.
- Model inference integration with backend APIs.

### Full-Stack Application

- Component management interface.
- REST API integration.
- Maintenance analytics dashboard.
- Lifecycle history visualisation.
- Reporting and user-facing analytics.

These are planned capabilities and should not be interpreted as already implemented functionality.

## 4. Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Backend | Python, FastAPI | Implemented foundation |
| Database | PostgreSQL 16 | Configured |
| ORM | SQLAlchemy | Configured |
| Database migrations | Alembic | Initial migration created |
| Database driver | Psycopg | Configured |
| Graph processing | NetworkX | Dependency available; application use planned |
| Containerisation | Docker, Docker Compose | Configured |
| API | REST, OpenAPI documentation | Initial API available |
| Frontend | React, TypeScript | Planned |
| Data processing and ML | Pandas, NumPy, Scikit-learn | Planned |

## 5. Architecture

AeroTrace is documented at two levels: the **current deployment architecture**, which shows what is running today, and the **target application architecture**, which shows how the planned user interface and domain services will connect to the existing backend and database foundation.

### Current Deployment Architecture

The current Docker Compose environment contains the FastAPI backend and PostgreSQL database. The backend connects to PostgreSQL through SQLAlchemy and Psycopg. Alembic applies database schema migrations, and PostgreSQL stores its data in a persistent named Docker volume.

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

    classDef implemented fill:#e8f5ec,stroke:#27834a,color:#173d25,stroke-width:1.5px;
    class Client,API,DB,Volume,Migration implemented;
```

**Current components:** FastAPI, SQLAlchemy, Psycopg, PostgreSQL 16, Alembic, Docker Compose, and the persistent PostgreSQL volume. The API currently exposes the health-check route; component and lifecycle operations are not yet implemented as API endpoints.

### Target Application Architecture

The target architecture adds a React and TypeScript frontend and separates backend responsibilities into lifecycle management, data-integrity, and machine-learning services. These service modules, the frontend, and analytics outputs are planned; the diagram does not imply that they are already implemented.

```mermaid
flowchart TB
    User["User / Maintenance analyst"]
    UI["Frontend application<br/>React + TypeScript<br/>(planned)"]
    API["FastAPI REST API<br/>(backend foundation in place)"]

    subgraph Services["Application services — planned"]
        Lifecycle["Component lifecycle management<br/>Registration · installation · removal · history"]
        Integrity["Data integrity services<br/>Validation · relationship checks · audit rules"]
        ML["Machine learning and analytics<br/>Preprocessing · anomaly detection · prediction"]
    end

    ORM["SQLAlchemy persistence layer"]
    DB[("PostgreSQL 16")]
    History["Historical component lifecycle data"]
    Outputs["Analytics and visualisation<br/>Dashboards · reports · risk analysis<br/>(planned)"]

    User --> UI
    UI -.->|"REST / JSON"| API
    API -.-> Lifecycle
    API -.-> Integrity
    API -.-> ML
    Lifecycle -.-> ORM
    Integrity -.-> ORM
    ML -.->|"Read historical data"| ORM
    ORM --> DB
    DB --> History
    History -.-> Outputs
    ML -.->|"Model outputs"| Outputs

    classDef foundation fill:#e8f5ec,stroke:#27834a,color:#173d25,stroke-width:1.5px;
    classDef planned fill:#f4f4f5,stroke:#737373,color:#333333,stroke-dasharray:5 5;
    class User,API,ORM,DB,History foundation;
    class UI,Lifecycle,Integrity,ML,Outputs planned;
```

**Legend:** Solid green nodes identify the existing project foundation. Grey dashed nodes and dashed connections represent planned components or integrations.

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
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── entities.py
│   │   └── main.py
│   ├── migrations/
│   │   ├── versions/
│   │   │   └── 78282062446d_create_initial_core_tables.py
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/
│   │   ├── test_main.py
│   │   └── test_models.py
│   ├── .dockerignore
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

For direct local backend execution, create `backend/.env` with a connection string for your local PostgreSQL instance:

```env
DATABASE_URL=postgresql+psycopg://aerotrace:your_password@localhost:5432/aerotrace
```

Use the actual username, password, host, and database configured in your environment. The direct-local connection string should match the database credentials used by PostgreSQL.

### Start the Application with Docker Compose

From the repository root:

```bash
docker compose up --build -d
```

Check the service status:

```bash
docker compose ps
```

The backend is available at `http://127.0.0.1:8000`, and PostgreSQL is exposed on port `5432`.

### Apply Database Migrations

Run the initial schema migration inside the backend container:

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

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Activate it on Windows Command Prompt:

```bat
.venv\Scripts\activate.bat
```

Activate it on Linux/macOS:

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

### API Documentation and Health Check

| Resource | URL |
|---|---|
| Interactive API documentation | http://127.0.0.1:8000/docs |
| OpenAPI schema | http://127.0.0.1:8000/openapi.json |
| Health check | http://127.0.0.1:8000/health |

The health endpoint reports the API service status. It is not currently a database-readiness or full application-dependency check.

## 8. Testing and Code Quality

From the `backend` directory, install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the test suite with coverage enforcement:

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

Run linting and formatting checks:

```bash
ruff check .
ruff format --check .
```

The GitHub Actions workflows run backend checks, migration validation, Docker image builds, and CodeQL analysis on their configured triggers. Review the Actions tab for the status of the latest runs.

## 9. Development Roadmap

### Backend and Database

- [x] Initial FastAPI backend setup.
- [x] Environment-based application configuration.
- [x] SQLAlchemy database foundation.
- [x] PostgreSQL 16 Docker Compose service with persistent storage.
- [x] Backend Dockerfile and container orchestration.
- [x] Initial relational schema for aircraft, engines, components, organisations, lifecycle events, and installations.
- [x] Alembic migration for the initial core tables.
- [x] Migration upgrade and schema-drift validation configured in backend CI.
- [x] Backend automated tests, coverage enforcement, and Ruff checks configured.
- [x] Docker image build validation configured in CI.
- [x] CodeQL workflow for Python and GitHub Actions configured.
- [ ] Component registration and retrieval APIs.
- [ ] Lifecycle event creation and query APIs.
- [ ] Installation and removal workflows.
- [ ] Maintenance and inspection record APIs.
- [ ] Authentication, authorisation, and audit controls.
- [ ] Query optimisation and expanded integration testing.

### Frontend

- [ ] React and TypeScript application.
- [ ] Component and aircraft management screens.
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

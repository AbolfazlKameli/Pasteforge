# PasteForge

**A lightweight, secure, and scalable paste-sharing service built with FastAPI.**

PasteForge is a backend-focused paste-sharing application that allows users to create, manage, and share text snippets
with syntax highlighting, configurable access permissions, and automatic expiration.

The project is designed with an emphasis on clean architecture, database design, security, performance, and
maintainability. It serves as a practical demonstration of backend engineering and system design principles.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [System Design & Documentation](#system-design--documentation)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Roadmap](#roadmap)

## Overview

PasteForge provides a simple way to store and share text snippets without unnecessary complexity.

Users can create pastes anonymously or through authenticated accounts. Each paste supports different access levels,
expiration policies, and syntax highlighting.

The application is designed around a modular backend architecture, separating API handling, business logic, data access,
and infrastructure concerns.

### Key Design Goals

- Clean separation of responsibilities.
- Secure authentication and authorization.
- Efficient database queries and caching.
- Reliable background task processing.
- Explicit business rules and data integrity.
- Maintainable and testable application architecture.

## Features

### Paste Management

- Create text pastes with syntax highlighting.
- Support for public, private, and password-protected pastes.
- Configurable expiration policies.
- Maximum content size of 1 MB per paste.
- Unique UUID-based paste identifiers.

### Anonymous Access

- Create and share pastes without registration.
- Anonymous pastes automatically expire after 10 minutes.
- Maximum of 10 anonymous pastes per IP address.
- Rate limiting of 10 paste creations per minute.
- Anonymous users cannot modify or delete their pastes.

### Authentication & Authorization

- JWT-based authentication.
- Access and refresh token support.
- Refresh token rotation and blacklisting.
- Session management.
- Ownership-based authorization.
- Secure password hashing.

### Expiration & Background Processing

- Configurable expiration for authenticated pastes (1 minute to 24 hours).
- Expired pastes become inaccessible immediately.
- A retention period allows owners to update expired pastes.
- Background jobs handle permanent deletion.

## Tech Stack

| Category                      |                                                        Technology                                                        |
|:------------------------------|:------------------------------------------------------------------------------------------------------------------------:|
| Language                      |      <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=FFD43B" alt="Python" height="30"/>       |
| Web Framework                 |     <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI" height="30"/>      |
| Database                      | <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL" height="30"/> |
| ORM                           | <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" height="30"/> |
| Database Migrations           |     <img src="https://img.shields.io/badge/Alembic-6BA81E?logo=alembic&logoColor=white" alt="Alembic" height="30"/>      |
| Cache                         |        <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white" alt="Redis" height="30"/>         |
| Background Tasks              |       <img src="https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white" alt="Celery" height="30"/>       |
| Application Server            |     <img src="https://img.shields.io/badge/Uvicorn-499848?logo=gunicorn&logoColor=white" alt="Uvicorn" height="30"/>     |
| Reverse Proxy / Load Balancer |        <img src="https://img.shields.io/badge/NGINX-009639?logo=nginx&logoColor=white" alt="NGINX" height="30"/>         |
| Authentication                |      <img src="https://img.shields.io/badge/JWT-000000?logo=jsonwebtokens&logoColor=white" alt="JWT" height="30"/>       |
| Dependency Management         |           <img src="https://img.shields.io/badge/uv-DE5FE9?logo=astral&logoColor=white" alt="uv" height="30"/>           |

## System Design & Documentation

System design and technical decisions are documented separately to keep the implementation maintainable and the
architecture easy to understand.

All documentation is available in the [`System Design`](docs/System%20Design) directory.

| Document                                                                | Description                                                                                                |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [Requirements](docs/System%20Design/01-Requirements.md)                 | Functional and non-functional requirements, business rules, security constraints, and performance targets. |
| [System Architecture](docs/System%20Design/02-System%20Architecture.md) | High-level and detailed architecture, component responsibilities, and infrastructure design.               |
| [Database Design](docs/System%20Design/03-Database%20Design.md)         | Database entities, attributes, relationships, constraints, indexes, and normalization decisions.           |
| [ERD](docs/System%20Design/04-ERD.md)                                   | Entity Relationship Diagram illustrating database relationships.                                           |
| [API Design](docs/System%20Design/05-API%20Design.md)                   | API endpoints, request and response structures, and endpoint behavior.                                     |

### Architecture Highlights

- **Layered Architecture:** Separation of API, services, repositories, and infrastructure.
- **Cache-Aside Pattern:** Redis is used to improve read performance.
- **Source of Truth:** PostgreSQL is responsible for persistent data.
- **Background Processing:** Scheduled jobs handle expiration and cleanup operations.
- **Scalability:** NGINX distributes incoming traffic across application instances.

## Project Structure

PasteForge follows a modular architecture with clear separation of concerns across API, business logic, data access, and
infrastructure layers.

```text
PasteForge/
├── docs/
│   └── System Design/
│       ├── 01-Requirements.md
│       ├── 02-System Architecture.md
│       ├── 03-Database Design.md
│       ├── 04-ERD.md
│       └── 05-API Design.md
│
├── nginx/
│   ├── nginx.conf
│   └── pasteforge.conf
│
├── pasteforge/
│   ├── api/
│   │   ├── dependencies/
│   │   ├── middlewares/
│   │   ├── pagination/
│   │   └── v1/
│   │       └── routers/
│   │
│   ├── core/
│   │   ├── exceptions/
│   │   ├── config.py
│   │   ├── loggers.py
│   │   └── security.py
│   │
│   ├── db/
│   │   ├── migrations/
│   │   ├── database.py
│   │   └── celery_database.py
│   │
│   ├── infrastructure/
│   │   ├── email.py
│   │   ├── redis_pool.py
│   │   └── worker.py
│   │
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   ├── tasks/
│   ├── dependencies.py
│   └── main.py
│
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── pyproject.toml
├── uv.lock
└── README.md
```

### Directory Responsibilities

| Directory / File  | Responsibility                                                                  |
|-------------------|---------------------------------------------------------------------------------|
| `api/`            | API routing, request dependencies, middleware, and pagination.                  |
| `core/`           | Application configuration, security utilities, logging, and exception handling. |
| `db/`             | Database connections, Celery database configuration, and Alembic migrations.    |
| `infrastructure/` | External infrastructure integrations, including Redis, email, and Celery.       |
| `models/`         | SQLAlchemy database models.                                                     |
| `repositories/`   | Database access and persistence operations.                                     |
| `schemas/`        | Request validation and response serialization.                                  |
| `services/`       | Application business logic and service-layer operations.                        |
| `tasks/`          | Asynchronous and scheduled background tasks.                                    |
| `nginx/`          | NGINX reverse proxy and server configuration.                                   |
| `docs/`           | System design and technical documentation.                                      |

### Root Configuration Files

| File                 | Responsibility                                             |
|----------------------|------------------------------------------------------------|
| `Dockerfile`         | Defines the application container image.                   |
| `docker-compose.yml` | Defines and orchestrates the application services.         |
| `entrypoint.sh`      | Container startup and initialization commands.             |
| `alembic.ini`        | Alembic migration configuration.                           |
| `pyproject.toml`     | Project metadata and dependency configuration.             |
| `uv.lock`            | Locked dependency versions for reproducible installations. |

## Getting Started

```bash
git clone https://github.com/AbolfazlKameli/PasteForge.git

cd PasteForge
```

### Run with Docker Compose

Make sure Docker and Docker Compose are installed, then run the following command from the project root:

```bash
docker compose --env-file env/.env up
```

This command starts the services defined in `docker-compose.yml` using the environment configuration from `env/.env`.

To run the services in detached mode:

```bash
docker compose --env-file env/.env up -d
```

To stop the services:

```bash
docker compose down
```

### Run Locally

### Prerequisites

Make sure you have the following installed:

- Python 3.12+
- PostgreSQL
- Redis
- uv

#### 1. Install Dependencies

```bash
uv sync
```

#### 2. Configure Environment Variables

Create a `.env` file in the `env` directory and configure the required application settings.

See the [Environment Variables](#environment-variables) section.

#### 3. Run Database Migrations

```bash
uv run alembic upgrade head
```

#### 4. Start the Application

```bash
uv run uvicorn pasteforge.main:app --reload
```

The API should now be accessible at:

```text
http://localhost:8000
```

Interactive API documentation (if enabled):

```text
http://localhost:8000/docs
```

#### 5. Start Background Workers

Start the background worker and scheduler in separate terminal sessions.

```bash
uv run celery -A pasteforge.infrastructure.worker worker -B -l info
```

## Environment Variables

The application uses separate environment files for each runtime environment:

```text
env/
├── .env
├── .dev.env
├── .test.env
└── .prod.env
```

`ENV_STATE` in `.env` selects the configuration: `development`, `test`, or `production`. Each environment file contains
the required database, Redis, email, Celery, security, and logging settings.

Update the placeholder values before running the application. Keep production secrets out of version control.

| File        | Purpose                         |
|:------------|:--------------------------------|
| `.env`      | Selects the runtime environment |
| `.dev.env`  | Local development settings      |
| `.test.env` | Isolated test settings          |
| `.prod.env` | Production settings             |

## Roadmap

The roadmap represents the planned development direction and can be updated as the project evolves.

Progress is tracked using GitHub-style task lists.

### Phase 1: Core Backend

- [x] Complete project configuration.
- [x] Implement database models and migrations.
- [x] Implement paste creation and retrieval.
- [x] Implement anonymous paste support.
- [x] Implement paste access permissions.
- [x] Implement paste expiration logic.

### Phase 2: Authentication & Security

- [x] Complete JWT authentication.
- [x] Implement refresh token rotation and blacklisting.
- [x] Implement session management.
- [x] Complete ownership-based authorization.
- [x] Implement password-protected pastes.
- [x] Review security-sensitive operations.

### Phase 3: Infrastructure & Performance

- [x] Implement Redis caching using Cache-Aside.
- [x] Complete rate-limiting mechanisms.
- [x] Implement background expiration and deletion jobs.
- [x] Configure NGINX.
- [x] Optimize database queries and indexes.

### Phase 4: Testing & Quality

- [ ] Write unit tests for core business logic.
- [ ] Write integration tests for API endpoints.
- [ ] Test authentication and authorization scenarios.
- [ ] Test expiration and background jobs.
- [ ] Add performance and load testing.
- [ ] Improve logging and observability.

### Phase 5: Deployment & Finalization

- [x] Add Docker support.
- [ ] Prepare production configuration.
- [ ] Set up CI/CD.
- [ ] Deploy the application.
- [x] Complete API documentation.
- [x] Finalize project documentation.

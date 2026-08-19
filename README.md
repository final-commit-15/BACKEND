# AgentForge Backend

Backend service for **AgentForge**, an AI-agent execution platform. The backend exposes the REST API used to manage users, agents, tasks, executions, integrations, webhooks, notifications, analytics, and related platform services.

> **Project status:** Backend implementation and verification completed as of **19 August 2026**.

## Overview

AgentForge Backend is built around:

- **FastAPI** for the HTTP API
- **PostgreSQL** for persistent application data
- **Redis** for messaging/cache infrastructure
- **Celery** for asynchronous background execution
- **SQLAlchemy async** for database access
- **JWT-based authentication** for API authorization
- Docker and Docker Compose for local deployment

The execution pipeline supports asynchronous agent execution through the backend and Celery worker.

## Architecture

```text
Client / Postman / Frontend
          |
          v
    FastAPI Backend
          |
    +-----+----------------------+
    |                            |
    v                            v
PostgreSQL                    Redis
    |                            |
    |                            v
    |                     Celery Worker
    |                            |
    +----------------------------+
                 |
                 v
          Agent Execution
```

### Main backend areas

```text
src/agentforge_backend/
├── api/
│   └── v1/                 # REST API endpoints
├── clients/                # External service clients
├── config/                 # Application configuration
├── db/                     # Database engine/session setup
├── middleware/             # CORS, errors, logging
├── models/                 # SQLAlchemy models
├── schemas/                # Pydantic request/response schemas
├── security/               # JWT and permission handling
├── services/               # Business logic
├── utils/                  # Exceptions and response helpers
└── websocket/              # WebSocket management
```

Background worker code is located under:

```text
src/agentforge_backend/workers/
```

## Core Capabilities

### Authentication

The backend provides authentication endpoints including:

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
```

Authentication uses bearer JWT access tokens.

Example registration request:

```json
{
  "email": "user@example.com",
  "username": "testuser",
  "password": "string",
  "full_name": "Test User"
}
```

After authentication, use the returned access token as:

```text
Authorization: Bearer <access_token>
```

### Agent Management

Agents can be created and managed through the API.

An agent contains information such as:

- name
- description
- agent type
- model
- active/inactive state
- owner
- project association

Supported agent types verified during backend testing include:

- `coding`
- `automation`
- `data`
- `research`

Agent ownership is enforced during execution. A user cannot execute another user's agent.

### Task and Execution Processing

The execution service is responsible for starting agent executions and coordinating execution state.

Typical execution lifecycle:

```text
queued
   |
   v
worker receives task
   |
   v
agent executes
   |
   v
completed
```

Failures are represented through the execution status/error fields.

The backend also supports execution lookup using the execution ID.

## Celery Worker

The worker handles asynchronous backend jobs.

Verified Celery tasks include:

```text
run_execution
send_notification
deliver_webhook
```

The worker connects to Redis and consumes the configured Celery queue.

Worker connectivity can be checked with:

```powershell
docker compose exec worker celery -A agentforge_backend.workers.celery_app inspect ping
```

A healthy worker returns a response similar to:

```text
pong
```

## Docker Setup

The backend is designed to run with Docker Compose.

### Services

The current Compose stack contains:

| Service | Purpose |
|---|---|
| `backend` | FastAPI application |
| `postgres` | PostgreSQL database |
| `redis` | Redis broker/infrastructure |
| `worker` | Celery background worker |

### Start the stack

Build and start everything:

```powershell
docker compose up -d --build
```

Check service status:

```powershell
docker compose ps
```

The verified healthy state is:

```text
backend      healthy
postgres     healthy
redis        healthy
worker       healthy
```

### View logs

Backend:

```powershell
docker compose logs -f backend
```

Worker:

```powershell
docker compose logs -f worker
```

PostgreSQL:

```powershell
docker compose logs -f postgres
```

Redis:

```powershell
docker compose logs -f redis
```

### Stop the stack

```powershell
docker compose down
```

## API Documentation

When the backend is running locally, FastAPI's interactive documentation is available at:

```text
http://localhost:8000/docs
```

OpenAPI JSON:

```text
http://localhost:8000/openapi.json
```

Health endpoint:

```text
http://localhost:8000/health
```

A successful health request returns HTTP `200`.

## Local Development

Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project dependencies using the repository's package configuration.

For a development server, use the project's configured FastAPI/Uvicorn entry point. The Docker Compose configuration remains the recommended way to verify the complete backend stack because execution depends on PostgreSQL, Redis, and Celery.

## Database

The application uses PostgreSQL with SQLAlchemy's asynchronous database stack.

The configured database URL follows the async PostgreSQL format:

```text
postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>
```

Inside Docker Compose, the PostgreSQL service hostname is:

```text
postgres
```

When running database-dependent tests directly from the Windows host, the database host must be reachable from the host environment rather than relying on the Docker service hostname.

## Testing

### Run the full test suite

```powershell
pytest -q
```

The backend verification completed with:

```text
4 passed
```

### Run database integration tests

From the repository environment:

```powershell
pytest tests/integration/test_db.py -q
```

The database integration test was also verified successfully after using a host-reachable PostgreSQL connection for the Windows-host test environment.

### Python compilation

```powershell
python -m compileall src
```

Result:

```text
Passed
```

### Dependency verification

```powershell
pip check
```

Result:

```text
No broken requirements found
```

### Static type checking

```powershell
mypy src
```

Result:

```text
Success: no issues found
```

The final type-checking run covered 86 source files.

## Verified Error Handling

The backend execution API was tested against several invalid and edge-case scenarios.

| Scenario | Expected/Verified result |
|---|---|
| Valid UUID | Accepted |
| Invalid UUID | HTTP 422 |
| Nonexistent agent | HTTP 404 |
| Nonexistent task | HTTP 404 |
| Disabled agent | HTTP 403 |
| Missing execution | HTTP 404 |
| Missing/invalid authentication | Authentication failure |
| Unsupported DELETE execution route | HTTP 405 |

Agent ownership is also enforced, preventing one user from executing an agent belonging to another user.

## Execution Verification

The backend execution pipeline was verified with:

- Coding Agent execution
- Automation Agent execution
- Data Agent execution
- Research Agent execution
- Five concurrent execution tests
- Worker restart recovery
- Post-restart execution
- Fresh execution after a clean Docker rebuild

The final clean-stack execution successfully moved from:

```text
queued → completed
```

with:

```text
error: null
```

and a non-null agent output.

## Worker Recovery Verification

The Celery worker was intentionally restarted and then checked for recovery.

Verification included:

```powershell
docker compose restart worker
```

followed by:

```powershell
docker compose exec worker celery -A agentforge_backend.workers.celery_app inspect ping
```

The worker successfully reconnected to Redis and resumed execution.

## Code Quality and Verification Summary

| Verification | Result |
|---|---|
| Automated tests | ✅ 4 passed |
| Python compilation | ✅ Passed |
| `pip check` | ✅ No broken requirements |
| `mypy src` | ✅ No issues |
| Backend Docker image | ✅ Built |
| Backend container | ✅ Healthy |
| PostgreSQL | ✅ Healthy |
| Redis | ✅ Healthy |
| Celery worker | ✅ Healthy |
| Worker restart recovery | ✅ Passed |
| End-to-end execution | ✅ Passed |

## Important Development Notes

### Execution service

The execution service should now be treated as a **verified baseline**. Avoid making additional changes unless a new regression or requirement appears.

### Database reset during clean verification

A clean Docker/database rebuild created a fresh database state. Previous test users, agents, and tasks were therefore no longer present.

For the final end-to-end verification:

1. A new test user was registered.
2. A new Coding Agent was created for that user.
3. A fresh execution was submitted.
4. The execution completed successfully.

This was expected behavior for a fresh database and was not treated as an application defect.

## Useful Commands

### Check all containers

```powershell
docker compose ps
```

### Rebuild everything

```powershell
docker compose up -d --build
```

### Restart worker

```powershell
docker compose restart worker
```

### Check Celery worker

```powershell
docker compose exec worker celery -A agentforge_backend.workers.celery_app inspect ping
```

### Run tests

```powershell
pytest -q
```

### Compile source

```powershell
python -m compileall src
```

### Check dependencies

```powershell
pip check
```

### Run mypy

```powershell
mypy src
```

## Repository Status

As of 19 August 2026:

```text
agentforge-shared          ✅ COMPLETE
agentforge-ai-services    ✅ COMPLETE
agentforge-agents         ✅ COMPLETE
agentforge-integrations   ✅ COMPLETE
agentforge-backend        ✅ COMPLETE
agentforge-frontend       ⏳ PENDING
agentforge-docs           ⏳ PENDING
agentforge-infra          ⏳ PENDING
```

### Next Recommended Work

The backend is now a verified baseline.

The next recommended repository is:

```text
agentforge-docs
```

Followed by the remaining frontend and infrastructure work according to the overall AgentForge project plan.

---

**AgentForge Backend — Completed and verified by Ajay**  
**Last updated: 19 August 2026**

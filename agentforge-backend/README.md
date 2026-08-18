# AgentForge Backend

Central orchestration API for AgentForge platform.

## Quick Start

1. Copy `.env.example` to `.env` and adjust.
2. Run `docker compose up --build`.
3. API at `http://localhost:8000`.
4. Health: `/health`, `/health/live`, `/health/ready`.

## API Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Testing

```bash
poetry run pytest
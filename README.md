# AgentForge Backend

Production-ready SaaS backend API for AgentForge — multi-tenant workspace architecture with PostgreSQL, Redis, Alembic migrations, and JWT authentication.

## Architecture

```
BACKEND/
├── agentforge-backend/          # Main FastAPI application
│   ├── src/agentforge_backend/  # Source code
│   │   ├── api/v1/             # REST endpoints (auth, users, workspaces, agents, tasks, etc.)
│   │   ├── models/             # SQLAlchemy 2.0 models (36 tables)
│   │   ├── services/           # Business logic
│   │   ├── security/           # JWT, passwords, permissions
│   │   ├── workers/            # Celery workers
│   │   ├── db/                 # Database session & Redis
│   │   ├── middleware/         # Rate limiting, CORS, logging, security headers
│   │   └── config/             # Pydantic settings
│   ├── migrations/             # Alembic migrations (auto-generated)
│   ├── Dockerfile              # Multi-stage build
│   ├── pyproject.toml          # Poetry dependencies
│   └── poetry.lock
├── docker-compose.yml          # Production stack
└── .env                        # Environment variables (not committed)
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.11+ for local development

### Production Deployment

```bash
cd BACKEND
cp agentforge-backend/.env.example agentforge-backend/.env
# Edit .env with secure values:
#   - POSTGRES_PASSWORD
#   - JWT_SECRET (generate with: openssl rand -hex 32)
#   - GOOGLE_CLIENT_ID/SECRET for OAuth

docker compose up --build -d
```

### Verify Deployment

```bash
# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready

# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","username":"admin","password":"SecurePass123","full_name":"Admin User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@company.com","password":"SecurePass123"}'

# Access protected endpoint
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/auth/me
```

### Local Development

```bash
cd agentforge-backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install poetry
poetry install

# Start PostgreSQL & Redis (via Docker)
docker compose up -d db redis

# Run migrations
ALEMBIC_DOCKER=0 poetry run alembic upgrade head

# Start server
poetry run uvicorn agentforge_backend.main:app --reload --host 0.0.0.0 --port 8000

# Start worker (separate terminal)
poetry run celery -A agentforge_backend.workers.celery_app worker --loglevel=info
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Backend API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Primary database (agentforge) |
| Redis | 6379 | Cache, Celery broker, token blacklist |

## Database

- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic (auto-runs on container startup)
- **Models**: 36 tables covering users, workspaces, agents, tasks, executions, integrations, webhooks, notifications, audit logs, OAuth, API keys, permissions, and more
- **Naming**: `agentforge` database, `agentforge` user

## Authentication

- **JWT Access Tokens**: 30 min expiry, HS256
- **Refresh Tokens**: 7 days, stored in DB with rotation
- **Password Hashing**: Argon2 (preferred) + bcrypt fallback
- **Token Blacklist**: Redis-based with TTL
- **Session Tracking**: Device info, IP, user agent
- **MFA Support**: TOTP with backup codes

## Workspace Architecture (Multi-tenant)

- Users belong to multiple workspaces
- Roles: Owner, Admin, Member, Viewer
- Workspace creation: Owner/Admin only
- Invitations: Email-based with token
- Personal workspaces: Auto-created on signup
- Enterprise: Domain verification support (Google OAuth)

## API Endpoints (v1)

```
/api/v1/auth/*           # Register, login, refresh, logout, me
/api/v1/users/*          # User management
/api/v1/workspaces/*     # Workspace CRUD, members, invitations, settings
/api/v1/agents/*         # Agent CRUD, versions, execution
/api/v1/tasks/*          # Task management, comments, attachments
/api/v1/projects/*       # Project CRUD
/api/v1/executions/*     # Execution monitoring, logs, metrics
/api/v1/integrations/*   # Third-party integrations (GitHub, Slack, etc.)
/api/v1/webhooks/*       # Webhook management, deliveries
/api/v1/notifications/*  # User notifications
/api/v1/settings/*       # User & workspace settings
/api/v1/tools/*          # Tool registry
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_PASSWORD` | Yes | Database password |
| `JWT_SECRET` | Yes | JWT signing key (32+ chars) |
| `DATABASE_URL` | Auto | `postgresql+asyncpg://user:pass@db:5432/agentforge` |
| `REDIS_URL` | Auto | `redis://agentforge-redis:6379/0` |
| `CELERY_BROKER_URL` | Auto | `redis://agentforge-redis:6379/1` |
| `CELERY_RESULT_BACKEND` | Auto | `redis://agentforge-redis:6379/2` |
| `GOOGLE_CLIENT_ID` | No | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth |
| `CORS_ORIGINS` | No | JSON array of allowed origins |

## Database Access

```bash
# Inside container
docker compose exec db psql -U agentforge -d agentforge

# Common queries
\dt                    # List tables
\d users              # Describe users table
SELECT * FROM alembic_version;  # Current migration
```

## Monitoring

- **Prometheus metrics**: `/metrics` (if `METRICS_ENABLED=true`)
- **Health endpoints**: `/health`, `/health/live`, `/health/ready`
- **Structured logging**: JSON format with sensitive field redaction

## Security

- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- Rate limiting (login: 5/min, register: 3/min, default: 100/min)
- CORS configured via `CORS_ORIGINS`
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy ORM

## Troubleshooting

### Migration Issues
```bash
# Check migration status
docker compose exec backend python -m alembic current

# Reset database (DANGEROUS - destroys data)
docker compose exec db psql -U agentforge -d agentforge -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose restart backend
```

### Connection Issues
```bash
# Verify DB connectivity
docker compose exec backend python -c "from agentforge_backend.db.session import engine; print('OK')"

# Check Redis
docker compose exec backend python -c "from agentforge_backend.db.redis import get_redis_client; import asyncio; print(asyncio.run(get_redis_client()).ping())"
```

### Logs
```bash
docker compose logs -f backend
docker compose logs -f worker
docker compose logs -f db
```

## Production Checklist

- [ ] Strong `JWT_SECRET` (32+ random bytes)
- [ ] Strong `POSTGRES_PASSWORD`
- [ ] `ENVIRONMENT=production` in `.env`
- [ ] `CORS_ORIGINS` restricted to your domains
- [ ] HTTPS termination (reverse proxy: nginx/Traefik)
- [ ] Database backups configured
- [ ] Monitoring/alerting on health endpoints
- [ ] Log aggregation (ELK, Loki, etc.)

## License

Proprietary — AgentForge
# Faust — Architecture Overview

> Last Updated: 2026-03-14 by ARCHITECT

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Load Balancer / Nginx                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │   React SPA   │───▶│ FastAPI (v1) │───▶│  PostgreSQL 16       │   │
│  │  (TypeScript)  │    │    :8000      │    │  (async via asyncpg) │   │
│  └──────────────┘    └──────┬───────┘    └──────────────────────┘   │
│                              │                                       │
│                              │ Celery dispatch                       │
│                              ▼                                       │
│                        ┌───────────┐                                 │
│                        │   Redis   │                                 │
│                        │  (broker) │                                 │
│                        └─────┬─────┘                                 │
│                              │                                       │
│                    ┌─────────▼──────────┐                            │
│                    │   Celery Workers    │                            │
│                    │                     │                            │
│                    │  ┌─────┐ ┌───────┐ │                            │
│                    │  │Nmap │ │Nuclei │ │                            │
│                    │  └─────┘ └───────┘ │                            │
│                    │  ┌─────┐ ┌──────┐  │                            │
│                    │  │Trivy│ │ DAST │  │                            │
│                    │  └─────┘ └──────┘  │                            │
│                    └────────────────────┘                             │
│                              │                                       │
│                    ┌─────────▼──────────┐                            │
│                    │   AI Providers      │                            │
│                    │  OpenAI / Anthropic │                            │
│                    │  Google / Ollama    │                            │
│                    └────────────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### API Layer (`app/api/`)
- FastAPI with versioned routers (`/api/v1/`)
- Request validation via Pydantic schemas
- JWT authentication + RBAC authorization
- CORS configured per-environment
- OpenAPI/Swagger docs disabled in production

### Core Layer (`app/core/`)
- **config.py** — Pydantic Settings, all config from env vars
- **database.py** — Async SQLAlchemy engine (asyncpg), session factory
- **security.py** — JWT creation/validation, bcrypt hashing, RBAC
- **logging.py** — Structured logging (JSON in prod, readable in dev)

### Models Layer (`app/models/`)
- SQLAlchemy 2.0 ORM with mapped_column
- UUID primary keys (gen_random_uuid server-side)
- Timestamp mixins (created_at, updated_at)
- Relationships enforce cascade deletes

### Scanning Layer (`app/scanners/`)
- Each scanner is a separate module (nmap, nuclei, trivy, dast)
- Scanners run inside Celery workers with timeouts
- Results are parsed and stored as Finding records
- Scan targets validated against project.allowed_targets

### AI Layer (`app/ai/`)
- Pluggable provider system (no vendor lock-in)
- Remediation engine generates fix guidance
- Triage engine computes composite risk scores
- All AI calls are async with retries

### Services Layer (`app/services/`)
- Business logic separated from API endpoints
- Scan orchestration via Celery tasks
- Report generation pipeline

## Key Design Decisions

1. **Async everywhere** — asyncpg + async SQLAlchemy for DB, httpx for external APIs
2. **Multi-tenant by default** — Project model acts as isolation boundary
3. **Scan safety** — CIDR allowlist per project prevents unauthorized scanning
4. **Hierarchical RBAC** — admin > analyst > viewer, enforced at API layer
5. **Denormalized counts** — Finding/severity counts on Scan and Asset for dashboard performance
6. **Celery for heavy work** — Scans and report generation run as background tasks

## Security Posture

- JWT tokens with type claims (access vs refresh) to prevent confusion attacks
- Refresh tokens omit role — force re-fetch from DB on every refresh
- bcrypt cost 12 (OWASP minimum)
- Login errors intentionally vague (prevent user enumeration)
- OpenAPI docs disabled in production
- CORS restricted to configured origins
- Scan targets validated against project allowlist
- Non-root Docker container

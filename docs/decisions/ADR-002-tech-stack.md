# ADR-002: Tech Stack

**Status:** Accepted  
**Date:** 2026-03-14  
**Decision Maker:** ARCHITECT

## Context

We need a tech stack that supports:
- High-concurrency async I/O (scanning, AI API calls)
- Type safety and developer ergonomics
- Modern web UI
- Easy self-hosting (Docker)
- Strong ecosystem for security tooling

## Decision

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python + FastAPI | 3.12+ / 0.115+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| DB Driver (app) | asyncpg | 0.29+ |
| DB Driver (migrations) | psycopg2-binary | 2.9+ |
| Database | PostgreSQL | 16 |
| Task Queue | Celery + Redis | 5.3+ / 7+ |
| Frontend | React + TypeScript + TailwindCSS | 18+ |
| Auth | JWT (python-jose) + bcrypt (passlib) | |
| HTTP Client | httpx (async) | 0.27+ |
| Deployment | Docker Compose (dev), Kubernetes (prod) | |

## Rationale

### Why Python + FastAPI (not Go, not Node)
- **Python dominates security tooling** — nmap, nuclei, trivy all have Python wrappers
- **FastAPI** is the fastest Python web framework with native async support
- **Type hints** + Pydantic give us compile-time-like safety
- Go would be faster but has a smaller security tooling ecosystem
- Node/Express has weaker typing and fewer security libraries

### Why asyncpg (not psycopg2 for app queries)
- asyncpg is 3-5x faster than psycopg2 for async workloads
- Native async/await support with SQLAlchemy 2.0
- psycopg2 kept only for Alembic (which requires sync driver)

### Why PostgreSQL 16 (not MySQL, not MongoDB)
- JSONB columns for flexible scanner output
- Array columns for allowed_targets
- Row-level security for future multi-tenancy
- UUID gen_random_uuid() for server-side PK generation
- Excellent full-text search for finding queries

### Why Celery (not asyncio tasks, not Dramatiq)
- Celery is battle-tested for long-running tasks (scans can take hours)
- Built-in retry, rate limiting, and task revocation
- Redis as broker is simple and fast
- Better monitoring (Flower) than alternatives

### Why React + TypeScript (not Vue, not Svelte)
- Largest ecosystem and talent pool
- TypeScript ensures type safety across the stack
- TailwindCSS for rapid UI development
- Rich component libraries (shadcn/ui, Radix)

## Consequences

- All Python code must use type hints
- All TypeScript must use strict mode
- Async/await is the default pattern for I/O
- Docker is required for development (no bare-metal setup)

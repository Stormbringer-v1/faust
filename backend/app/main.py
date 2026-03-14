"""
Faust — FastAPI application entrypoint.

This is the main application factory. It wires up:
- CORS middleware
- Request ID middleware
- API routers (v1)
- Startup/shutdown lifecycle hooks (admin seed)
- Health check endpoint
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api.v1 import api_v1_router
from app.middleware.request_id import RequestIDMiddleware

settings = get_settings()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: startup and shutdown hooks."""
    # ── Startup ──────────────────────────────────────────────────────
    setup_logging()
    logger.info(
        "Faust %s starting (env=%s, debug=%s)",
        settings.APP_VERSION,
        settings.ENVIRONMENT,
        settings.DEBUG,
    )

    # Seed first admin user if configured
    if settings.FIRST_ADMIN_PASSWORD:
        from app.core.database import async_session_factory
        from app.services.seed import seed_first_admin
        async with async_session_factory() as db:
            await seed_first_admin(db)

    yield

    # ── Shutdown ─────────────────────────────────────────────────────
    logger.info("Faust shutting down")
    from app.core.database import engine
    await engine.dispose()


from app.core.rate_limit import setup_rate_limiting

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise-grade vulnerability management platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Setup SlowAPI rate limiting exception handlers
setup_rate_limiting(app)


# ── Middleware (order matters: outermost added last via add_middleware) ────────
# Request IDs go on first so every response including CORS errors gets the header
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# ── Health check (unauthenticated) ───────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

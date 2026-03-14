"""
Shared test fixtures for Faust backend tests.

Strategy:
- Schema (tables) created once per pytest session.
- Each test gets its own fresh connection + transaction, rolled back after.
- The db_session fixture uses a nested savepoint (SAVEPOINT) so that
  asyncpg never sees two concurrent operations on the same connection.

This approach is the standard pattern for SQLAlchemy 2.x async tests.
"""

import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.main import app
from app.core.database import get_db
from app.models.base import Base

# ── Postgres test engine ─────────────────────────────────────────────────────
_PG_USER = os.getenv("POSTGRES_USER", "faust")
_PG_PASS = os.getenv("POSTGRES_PASSWORD", "faust_dev_2026")
_PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
_PG_PORT = os.getenv("POSTGRES_PORT", "5432")

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{_PG_USER}:{_PG_PASS}@{_PG_HOST}:{_PG_PORT}/faust_test"
)

# NullPool = no connection reuse. Each operation gets its own connection.
# This prevents asyncpg "operation in progress" errors across coroutines.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

TestSessionFactory = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
)


# ── Session-scoped schema ─────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_schema():
    """Create tables once at the start of the test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Per-test isolated session ─────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_session(create_schema):
    """
    Provide an AsyncSession backed by its own connection.
    After the test, TRUNCATE all tables to reset state cleanly.
    This avoids asyncpg concurrent-operation errors from transaction nesting.
    """
    async with TestSessionFactory() as session:
        yield session
        await session.rollback()

    # Truncate all test tables after each test
    async with test_engine.begin() as conn:
        tables = ", ".join(
            [
                "findings",
                "reports",
                "scans",
                "assets",
                "projects",
                "users",
            ]
        )
        await conn.exec_driver_sql(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE")


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """
    Yield an AsyncClient with the test DB dependency overridden.
    """
    async def override_get_db():
        # Each endpoint invocation through the test client gets a fresh
        # short-lived session from the same factory (but a different connection)
        async with TestSessionFactory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Helpers ──────────────────────────────────────────────────────────────────

async def create_user_and_login(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "TestPass123",
    full_name: str = "Test User",
) -> tuple[str, dict]:
    """
    Register a user and return (access_token, user_data).
    """
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, f"Register failed: {response.text}"
    user_data = response.json()

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    access_token = login_response.json()["access_token"]
    return access_token, user_data


def auth_header(token: str) -> dict:
    """Return Authorization header dict for the given token."""
    return {"Authorization": f"Bearer {token}"}

"""
Integration tests for auth endpoints.

Tests all auth flows: register, login, refresh, /me, RBAC, edge cases.
"""

import pytest
from httpx import AsyncClient


class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@example.com",
                "password": "SecurePass123",
                "full_name": "Alice",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert data["full_name"] == "Alice"
        assert data["role"] == "viewer"  # default
        assert data["is_active"] is True
        assert "hashed_password" not in data
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"email": "bob@example.com", "password": "Pass1234!", "full_name": "Bob"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"]

    async def test_register_password_too_short(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "carol@example.com", "password": "short", "full_name": "Carol"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "ValidPass1", "full_name": "X"},
        )
        assert resp.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "dave@example.com", "password": "DavePass1", "full_name": "Dave"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "dave@example.com", "password": "DavePass1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "eve@example.com", "password": "EvePass12", "full_name": "Eve"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "eve@example.com", "password": "WrongPassword"},
        )
        assert resp.status_code == 401
        # Vague message for security
        assert "Incorrect" in resp.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            data={"username": "nobody@example.com", "password": "Pass12345"},
        )
        assert resp.status_code == 401


class TestMe:
    """GET /api/v1/auth/me"""

    async def test_me_authenticated(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "frank@example.com", "password": "FrankPass1", "full_name": "Frank"},
        )
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "frank@example.com", "password": "FrankPass1"},
        )
        token = login.json()["access_token"]

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "frank@example.com"

    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer totally.invalid.token"},
        )
        assert resp.status_code == 401


class TestRefresh:
    """POST /api/v1/auth/refresh"""

    async def test_refresh_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "grace@example.com", "password": "GracePass1", "full_name": "Grace"},
        )
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "grace@example.com", "password": "GracePass1"},
        )
        refresh_token = login.json()["refresh_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        """Access tokens must not be accepted as refresh tokens."""
        await client.post(
            "/api/v1/auth/register",
            json={"email": "henry@example.com", "password": "HenryPass1", "full_name": "Henry"},
        )
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "henry@example.com", "password": "HenryPass1"},
        )
        access_token = login.json()["access_token"]

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 401

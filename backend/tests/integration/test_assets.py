"""
Integration tests for asset endpoints.

Assets are project-scoped. Tests verify RBAC, CRUD, identifier uniqueness.
Note: All test users have 'viewer' role by default, so create_asset (analyst+) gets 403.
These tests focus on the shape of available responses and access controls.
"""

import uuid
import pytest
from httpx import AsyncClient

from tests.conftest import create_user_and_login, auth_header


class TestAssetRBAC:
    """Asset write endpoints require analyst+ role."""

    async def test_create_asset_requires_analyst(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer-assets@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000001"
        resp = await client.post(
            f"/api/v1/projects/{fake_project}/assets/",
            json={
                "asset_type": "host",
                "identifier": "192.168.1.1",
            },
            headers=auth_header(token),
        )
        assert resp.status_code == 403

    async def test_list_assets_requires_auth(self, client: AsyncClient):
        fake_project = "00000000-0000-0000-0000-000000000001"
        resp = await client.get(f"/api/v1/projects/{fake_project}/assets/")
        assert resp.status_code == 401

    async def test_list_assets_nonexistent_project(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer2-assets@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000002"
        resp = await client.get(
            f"/api/v1/projects/{fake_project}/assets/",
            headers=auth_header(token),
        )
        # 404 — project doesn't exist
        assert resp.status_code == 404

    async def test_delete_asset_requires_analyst(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer3-assets@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000003"
        fake_asset = "00000000-0000-0000-0000-000000000004"
        resp = await client.delete(
            f"/api/v1/projects/{fake_project}/assets/{fake_asset}",
            headers=auth_header(token),
        )
        assert resp.status_code == 403


class TestAssetServiceIdentifier:
    """Unit tests for asset identifier uniqueness."""

    async def test_duplicate_identifier_rejected(self, db_session):
        from app.models.user import User
        from app.models.project import Project
        from app.services.asset_service import create_asset
        from app.schemas.asset import AssetCreate
        from app.models.asset import AssetType
        from app.core.security import hash_password
        from fastapi import HTTPException

        # Create user + project
        user = User(
            email="assettest@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="AssetTest",
        )
        db_session.add(user)
        await db_session.flush()

        project = Project(
            name="Asset Project",
            description="",
            owner_id=user.id,
        )
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        asset_data = AssetCreate(
            asset_type=AssetType.HOST,
            identifier="192.168.1.50",
        )

        # First creation should succeed
        asset = await create_asset(
            db_session, project.id, asset_data, user.id, "viewer"
        )
        assert asset.identifier == "192.168.1.50"

        # Second creation with same identifier should fail
        with pytest.raises(HTTPException) as exc:
            await create_asset(
                db_session, project.id, asset_data, user.id, "viewer"
            )
        assert exc.value.status_code == 409

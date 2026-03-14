"""
Unit tests for service layer.

Tests business logic in isolation with in-memory DB.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password


class TestUserService:
    """Tests for user_service module."""

    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        from app.services.user_service import get_user_by_id
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_user_by_id(db_session, uuid.uuid4())
        assert exc_info.value.status_code == 404

    async def test_list_users_empty(self, db_session: AsyncSession):
        from app.services.user_service import list_users
        users, total = await list_users(db_session)
        assert users == []
        assert total == 0

    async def test_create_and_get_user(self, db_session: AsyncSession):
        from app.models.user import User
        from app.services.user_service import get_user_by_id

        user = User(
            email="test@example.com",
            hashed_password=hash_password("TestPass1"),
            full_name="Test",
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        fetched = await get_user_by_id(db_session, user.id)
        assert fetched.email == "test@example.com"


class TestProjectService:
    """Tests for project_service module."""

    async def test_validate_cidr_valid(self):
        from app.services.project_service import _validate_cidr_list
        # Should not raise
        _validate_cidr_list(["192.168.0.0/24", "10.0.0.0/8", "2001:db8::/32"])

    async def test_validate_cidr_invalid(self):
        from app.services.project_service import _validate_cidr_list
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            _validate_cidr_list(["not-a-cidr"])
        assert exc.value.status_code == 422

    async def test_create_project(self, db_session: AsyncSession):
        from app.models.user import User
        from app.services.project_service import create_project
        from app.schemas.project import ProjectCreate

        # Create owner
        user = User(
            email="owner@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="Owner",
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        project_data = ProjectCreate(
            name="My Project",
            description="Testing",
            allowed_targets=["192.168.1.0/24"],
        )
        project = await create_project(db_session, project_data, user.id)
        assert project.name == "My Project"
        assert project.owner_id == user.id
        assert project.allowed_targets == ["192.168.1.0/24"]

    async def test_create_project_invalid_cidr(self, db_session: AsyncSession):
        from app.models.user import User
        from app.services.project_service import create_project
        from app.schemas.project import ProjectCreate
        from fastapi import HTTPException

        user = User(
            email="owner2@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="Owner2",
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)

        project_data = ProjectCreate(
            name="Bad Project",
            description="",
            allowed_targets=["invalid-cidr"],
        )
        with pytest.raises(HTTPException) as exc:
            await create_project(db_session, project_data, user.id)
        assert exc.value.status_code == 422


class TestScanService:
    """Tests for scan_service target validation logic."""

    async def test_target_within_allowlist(self):
        from app.services.scan_service import _validate_targets_within_allowlist
        # Should not raise
        _validate_targets_within_allowlist(["192.168.1.50"], ["192.168.1.0/24"])

    async def test_target_outside_allowlist(self):
        from app.services.scan_service import _validate_targets_within_allowlist
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            _validate_targets_within_allowlist(["10.0.0.1"], ["192.168.1.0/24"])
        assert exc.value.status_code == 403

    async def test_cidr_target_within_allowlist(self):
        from app.services.scan_service import _validate_targets_within_allowlist
        # 192.168.1.0/25 is a subnet of 192.168.1.0/24
        _validate_targets_within_allowlist(["192.168.1.0/25"], ["192.168.1.0/24"])

    async def test_cidr_target_outside_allowlist(self):
        from app.services.scan_service import _validate_targets_within_allowlist
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            # /8 is broader than /24 — not allowed
            _validate_targets_within_allowlist(["10.0.0.0/8"], ["192.168.1.0/24"])
        assert exc.value.status_code == 403

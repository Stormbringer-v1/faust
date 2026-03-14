"""
Integration tests for scan endpoints.

Scans require analyst+ to create/cancel/delete. Viewers can read.
Tests CIDR allowlist validation, state machine, and permissions.
"""

import uuid
import pytest
from httpx import AsyncClient

from tests.conftest import create_user_and_login, auth_header


class TestScanRBAC:
    """Scan write endpoints require analyst+ role."""

    async def test_create_scan_requires_analyst(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer-scans@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000001"
        resp = await client.post(
            f"/api/v1/projects/{fake_project}/scans/",
            json={"scan_type": "network"},
            headers=auth_header(token),
        )
        assert resp.status_code == 403

    async def test_cancel_scan_requires_analyst(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer2-scans@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000001"
        fake_scan = "00000000-0000-0000-0000-000000000002"
        resp = await client.post(
            f"/api/v1/projects/{fake_project}/scans/{fake_scan}/cancel",
            headers=auth_header(token),
        )
        assert resp.status_code == 403

    async def test_list_scans_requires_auth(self, client: AsyncClient):
        fake_project = "00000000-0000-0000-0000-000000000001"
        resp = await client.get(f"/api/v1/projects/{fake_project}/scans/")
        assert resp.status_code == 401

    async def test_list_scans_nonexistent_project_404(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer3-scans@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000003"
        resp = await client.get(
            f"/api/v1/projects/{fake_project}/scans/",
            headers=auth_header(token),
        )
        assert resp.status_code == 404


class TestScanTargetValidation:
    """Unit tests for CIDR allowlist enforcement."""

    async def test_empty_allowlist_blocks_scan(self, db_session):
        from app.models.user import User
        from app.models.project import Project
        from app.services.scan_service import create_scan
        from app.schemas.scan import ScanCreate
        from app.models.scan import ScanType
        from app.core.security import hash_password
        from fastapi import HTTPException

        user = User(
            email="scantest@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="ScanTest",
        )
        db_session.add(user)
        await db_session.flush()

        # Project with NO allowed_targets
        project = Project(
            name="No-Allowlist Project",
            description="",
            owner_id=user.id,
            allowed_targets=None,
        )
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        scan_data = ScanCreate(
            scan_type=ScanType.NETWORK,
            targets=["192.168.1.1"],
        )

        with pytest.raises(HTTPException) as exc:
            await create_scan(db_session, project.id, scan_data, user.id, "analyst")
        assert exc.value.status_code == 400
        assert "allowed_targets" in exc.value.detail

    async def test_target_outside_allowlist_blocked(self, db_session):
        from app.models.user import User
        from app.models.project import Project
        from app.services.scan_service import create_scan
        from app.schemas.scan import ScanCreate
        from app.models.scan import ScanType
        from app.core.security import hash_password
        from fastapi import HTTPException

        user = User(
            email="scantest2@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="ScanTest2",
        )
        db_session.add(user)
        await db_session.flush()

        project = Project(
            name="Allowlist Project",
            description="",
            owner_id=user.id,
            allowed_targets=["192.168.1.0/24"],
        )
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        scan_data = ScanCreate(
            scan_type=ScanType.NETWORK,
            targets=["10.0.0.1"],  # outside 192.168.1.0/24
        )

        with pytest.raises(HTTPException) as exc:
            await create_scan(db_session, project.id, scan_data, user.id, "analyst")
        assert exc.value.status_code == 403

    async def test_target_within_allowlist_creates_scan(self, db_session):
        from app.models.user import User
        from app.models.project import Project
        from app.services.scan_service import create_scan
        from app.schemas.scan import ScanCreate
        from app.models.scan import ScanType, ScanStatus
        from app.core.security import hash_password

        user = User(
            email="scantest3@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="ScanTest3",
        )
        db_session.add(user)
        await db_session.flush()

        project = Project(
            name="Valid Scan Project",
            description="",
            owner_id=user.id,
            allowed_targets=["192.168.1.0/24"],
        )
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        scan_data = ScanCreate(
            scan_type=ScanType.NETWORK,
            targets=["192.168.1.50"],
        )

        scan = await create_scan(db_session, project.id, scan_data, user.id, "analyst")
        assert scan.status == ScanStatus.PENDING
        assert scan.project_id == project.id

    async def test_scan_without_targets_creates_scan(self, db_session):
        """Scans with no explicit targets (scan all project assets) are always allowed."""
        from app.models.user import User
        from app.models.project import Project
        from app.services.scan_service import create_scan
        from app.schemas.scan import ScanCreate
        from app.models.scan import ScanType, ScanStatus
        from app.core.security import hash_password

        user = User(
            email="scantest4@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="ScanTest4",
        )
        db_session.add(user)
        await db_session.flush()

        project = Project(
            name="No-Target Scan Project",
            description="",
            owner_id=user.id,
            allowed_targets=None,  # no allowlist needed when no explicit targets
        )
        db_session.add(project)
        await db_session.flush()
        await db_session.refresh(project)

        scan_data = ScanCreate(
            scan_type=ScanType.NETWORK,
            targets=None,  # scan all assets
        )

        scan = await create_scan(db_session, project.id, scan_data, user.id, "analyst")
        assert scan.status == ScanStatus.PENDING


class TestScanStateManagement:
    """Test scan cancellation state machine."""

    async def test_cancel_only_pending_or_running(self, db_session):
        from app.models.user import User
        from app.models.project import Project
        from app.models.scan import Scan, ScanType, ScanStatus
        from app.services.scan_service import cancel_scan
        from app.core.security import hash_password
        from fastapi import HTTPException

        user = User(
            email="scancancel@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="ScanCancel",
        )
        db_session.add(user)
        await db_session.flush()

        project = Project(
            name="Cancel Test",
            description="",
            owner_id=user.id,
        )
        db_session.add(project)
        await db_session.flush()

        scan = Scan(
            project_id=project.id,
            initiated_by=user.id,
            scan_type=ScanType.NETWORK,
            status=ScanStatus.COMPLETED,  # already completed
        )
        db_session.add(scan)
        await db_session.flush()
        await db_session.refresh(scan)

        with pytest.raises(HTTPException) as exc:
            await cancel_scan(db_session, project.id, scan.id, user.id, "analyst")
        assert exc.value.status_code == 400
        assert "Cannot cancel" in exc.value.detail

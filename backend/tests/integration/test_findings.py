"""
Integration tests for finding endpoints.

Findings are read-only via the API (created by scanner workers).
Tests cover listing, filtering, triage, and access control.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import create_user_and_login, auth_header


class TestFindingRBAC:
    """Finding endpoint permissions."""

    async def test_list_findings_requires_auth(self, client: AsyncClient):
        fake_project = "00000000-0000-0000-0000-000000000001"
        resp = await client.get(f"/api/v1/projects/{fake_project}/findings/")
        assert resp.status_code == 401

    async def test_triage_requires_analyst(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer-findings@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000001"
        fake_finding = "00000000-0000-0000-0000-000000000002"
        resp = await client.patch(
            f"/api/v1/projects/{fake_project}/findings/{fake_finding}/triage",
            json={"status": "confirmed"},
            headers=auth_header(token),
        )
        assert resp.status_code == 403

    async def test_list_findings_empty_for_unknown_project(self, client: AsyncClient):
        token, _ = await create_user_and_login(client, "viewer2-findings@example.com", "Pass1234!")
        fake_project = "00000000-0000-0000-0000-000000000003"
        resp = await client.get(
            f"/api/v1/projects/{fake_project}/findings/",
            headers=auth_header(token),
        )
        # 404 — project not found
        assert resp.status_code == 404

    async def test_remediation_requires_auth(self, client: AsyncClient):
        fake_project = "00000000-0000-0000-0000-000000000001"
        fake_finding = "00000000-0000-0000-0000-000000000002"
        resp = await client.post(
            f"/api/v1/projects/{fake_project}/findings/{fake_finding}/remediation",
            json={"ai_provider": "ollama"},
        )
        assert resp.status_code == 401


class TestFindingTriage:
    """Unit tests for triage workflow."""

    async def test_triage_updates_audit_fields(self, db_session):
        from app.models.user import User
        from app.models.project import Project
        from app.models.asset import Asset, AssetType
        from app.models.scan import Scan, ScanType, ScanStatus
        from app.models.finding import Finding, FindingSeverity, FindingStatus
        from app.services.finding_service import triage_finding
        from app.schemas.finding import FindingTriage
        from app.core.security import hash_password
        import uuid

        # Setup user + project + asset + scan + finding
        user = User(
            email="triager-findings@example.com",
            hashed_password=hash_password("Pass1234!"),
            full_name="Triager",
        )
        db_session.add(user)
        await db_session.flush()

        project = Project(
            name="Finding Project",
            description="",
            owner_id=user.id,
        )
        db_session.add(project)
        await db_session.flush()

        asset = Asset(
            project_id=project.id,
            asset_type=AssetType.HOST,
            identifier="192.168.1.100",
        )
        db_session.add(asset)
        await db_session.flush()

        scan = Scan(
            project_id=project.id,
            initiated_by=user.id,
            scan_type=ScanType.NETWORK,
            status=ScanStatus.COMPLETED,
        )
        db_session.add(scan)
        await db_session.flush()

        finding = Finding(
            scan_id=scan.id,
            asset_id=asset.id,
            title="Test Vulnerability",
            description="A test vuln",
            severity=FindingSeverity.HIGH,
            status=FindingStatus.OPEN,
        )
        db_session.add(finding)
        await db_session.flush()
        await db_session.refresh(finding)

        # Triage it
        triage_data = FindingTriage(
            status=FindingStatus.CONFIRMED,
            triage_notes="Reviewed — legitimate finding",
        )
        triaged = await triage_finding(
            db_session, project.id, finding.id, triage_data, user.id, "analyst"
        )

        assert triaged.status == FindingStatus.CONFIRMED
        assert triaged.triaged_by == user.id
        assert triaged.triaged_at is not None
        assert triaged.triage_notes == "Reviewed — legitimate finding"

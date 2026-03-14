"""
Finding service — queries and triage for Finding model.

Findings are created by scanner workers, not via the API directly.
The API surface is: list (with filters), get detail, triage, request AI remediation.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finding import Finding, FindingSeverity, FindingStatus
from app.schemas.finding import FindingTriage
from app.services.project_service import get_project_by_id


async def get_finding_by_id(
    db: AsyncSession,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> Finding:
    """
    Fetch a finding by ID, verifying project access.

    Raises:
        HTTPException 404 if not found.
    """
    await get_project_by_id(db, project_id, user_id, user_role)

    # Join through scan to verify project ownership
    from app.models.scan import Scan
    result = await db.execute(
        select(Finding)
        .join(Scan, Finding.scan_id == Scan.id)
        .where(Finding.id == finding_id, Scan.project_id == project_id)
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding {finding_id} not found in project {project_id}",
        )
    return finding


async def list_findings(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    severity: FindingSeverity | None = None,
    finding_status: FindingStatus | None = None,
    cve_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Finding], int]:
    """
    List findings for a project with optional filters.

    Sorted by risk_score DESC (nulls last), then severity DESC.

    Returns:
        Tuple of (findings list, total count).
    """
    await get_project_by_id(db, project_id, user_id, user_role)

    from app.models.scan import Scan
    offset = (page - 1) * page_size

    base_stmt = (
        select(Finding)
        .join(Scan, Finding.scan_id == Scan.id)
        .where(Scan.project_id == project_id)
    )
    count_stmt = (
        select(func.count())
        .select_from(Finding)
        .join(Scan, Finding.scan_id == Scan.id)
        .where(Scan.project_id == project_id)
    )

    if severity is not None:
        base_stmt = base_stmt.where(Finding.severity == severity)
        count_stmt = count_stmt.where(Finding.severity == severity)
    if finding_status is not None:
        base_stmt = base_stmt.where(Finding.status == finding_status)
        count_stmt = count_stmt.where(Finding.status == finding_status)
    if cve_id is not None:
        base_stmt = base_stmt.where(Finding.cve_id == cve_id)
        count_stmt = count_stmt.where(Finding.cve_id == cve_id)

    # Sort: risk_score DESC (nulls last), created_at DESC as tiebreaker
    base_stmt = base_stmt.order_by(
        Finding.risk_score.desc().nulls_last(),
        Finding.created_at.desc(),
    ).offset(offset).limit(page_size)

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    result = await db.execute(base_stmt)
    return list(result.scalars().all()), total


async def triage_finding(
    db: AsyncSession,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    data: FindingTriage,
    triager_id: uuid.UUID,
    user_role: str,
) -> Finding:
    """
    Update the triage status of a finding, recording who triaged it and when.

    Raises:
        HTTPException 404 if not found.
    """
    finding = await get_finding_by_id(db, project_id, finding_id, triager_id, user_role)

    finding.status = data.status  # type: ignore[assignment]
    finding.triaged_by = triager_id
    finding.triaged_at = datetime.now(timezone.utc)
    if data.triage_notes is not None:
        finding.triage_notes = data.triage_notes

    await db.flush()
    await db.refresh(finding)
    return finding

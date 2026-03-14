"""
Scan service — lifecycle management for Scan model.

Creates scan records, validates targets against project allowlist,
and dispatches Celery tasks. Celery task IDs are stored for tracking.
"""

import ipaddress
import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.scan import Scan, ScanStatus, ScanType
from app.schemas.scan import ScanCreate, ScanStatusUpdate
from app.services.project_service import get_project_by_id


def _validate_targets_within_allowlist(
    targets: list[str],
    allowed_targets: list[str],
) -> None:
    """
    Ensure all scan targets fall within the project's allowed CIDR ranges.

    Raises:
        HTTPException 403 if any target is outside the allowlist.
    """
    allowed_networks = [
        ipaddress.ip_network(cidr, strict=False) for cidr in allowed_targets
    ]
    for target in targets:
        try:
            addr = ipaddress.ip_address(target)
        except ValueError:
            try:
                target_net = ipaddress.ip_network(target, strict=False)
                if not any(target_net.subnet_of(net) for net in allowed_networks):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Target {target!r} is outside project's allowed scan scope",
                    )
                continue
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid scan target: {target!r}",
                )
        if not any(addr in net for net in allowed_networks):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Target {target!r} is outside project's allowed scan scope",
            )


async def get_scan_by_id(
    db: AsyncSession,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> Scan:
    """
    Fetch a scan by ID within a project.

    Raises:
        HTTPException 404 if not found.
    """
    await get_project_by_id(db, project_id, user_id, user_role)

    result = await db.execute(
        select(Scan).where(Scan.id == scan_id, Scan.project_id == project_id)
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan {scan_id} not found in project {project_id}",
        )
    return scan


async def list_scans(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Scan], int]:
    """List scans in a project with pagination."""
    await get_project_by_id(db, project_id, user_id, user_role)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Scan).where(Scan.project_id == project_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_scan(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ScanCreate,
    initiator_id: uuid.UUID,
    user_role: str,
) -> Scan:
    """
    Create a Scan record and dispatch the Celery task.

    Validates targets against the project allowlist before queuing.

    Raises:
        HTTPException 403 if targets are outside the project's allowed scope.
        HTTPException 400 if project has no allowed_targets configured.
    """
    project = await get_project_by_id(db, project_id, initiator_id, user_role)

    # Target validation
    if data.targets:
        if not project.allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no allowed_targets configured. "
                       "Admin must set allowed_targets before scanning.",
            )
        _validate_targets_within_allowlist(data.targets, project.allowed_targets)

    scan = Scan(
        project_id=project_id,
        initiated_by=initiator_id,
        scan_type=data.scan_type,
        status=ScanStatus.PENDING,
        targets=json.dumps(data.targets) if data.targets else None,
        scanner_config=json.dumps(data.scanner_config) if data.scanner_config else None,
    )
    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    # Dispatch Celery task (import here to avoid circular imports at module level)
    try:
        from app.services.celery_app import dispatch_scan_task
        task_id = dispatch_scan_task(str(scan.id))
        scan.celery_task_id = task_id
        await db.flush()
    except ImportError:
        # Celery not configured yet — scan stays PENDING
        pass

    return scan


async def cancel_scan(
    db: AsyncSession,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> Scan:
    """
    Cancel a PENDING or RUNNING scan.

    Raises:
        HTTPException 400 if scan is not in a cancellable state.
    """
    scan = await get_scan_by_id(db, project_id, scan_id, user_id, user_role)

    cancellable = {ScanStatus.PENDING, ScanStatus.RUNNING}
    if scan.status not in cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel scan in state '{scan.status}'. "
                   "Only PENDING or RUNNING scans can be cancelled.",
        )

    # Revoke Celery task if we have the ID
    if scan.celery_task_id:
        try:
            from app.services.celery_app import revoke_task
            revoke_task(scan.celery_task_id)
        except ImportError:
            pass

    scan.status = ScanStatus.CANCELLED  # type: ignore[assignment]
    await db.flush()
    await db.refresh(scan)
    return scan


async def delete_scan(
    db: AsyncSession,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> None:
    """Delete a scan and cascade to its findings."""
    scan = await get_scan_by_id(db, project_id, scan_id, user_id, user_role)
    await db.delete(scan)
    await db.flush()

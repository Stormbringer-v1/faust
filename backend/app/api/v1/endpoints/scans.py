"""
Scans API — scan management within a project.

Scoped under /projects/{project_id}/scans.
Scan creation validates targets against project CIDR allowlist
and dispatches a Celery task.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload, require_analyst, require_viewer
from app.services import scan_service
from app.schemas.scan import ScanCreate, ScanResponse
from app.schemas.base import MessageResponse

router = APIRouter()


@router.post(
    "/",
    response_model=ScanResponse,
    status_code=201,
    summary="Launch a new scan",
    dependencies=[Depends(require_analyst)],
)
async def create_scan(
    project_id: uuid.UUID,
    body: ScanCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ScanResponse:
    """
    Launch a scan against project assets.

    Validates targets against project.allowed_targets CIDR list,
    creates a Scan record, and dispatches a Celery task.
    """
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await scan_service.create_scan(db, project_id, body, user_id, user_role)


@router.get(
    "/",
    response_model=list[ScanResponse],
    summary="List project scans",
    dependencies=[Depends(require_viewer)],
)
async def list_scans(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> list:
    """List scans in a project with pagination."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    scans, _ = await scan_service.list_scans(
        db, project_id, user_id, user_role, page=page, page_size=page_size
    )
    return scans


@router.get(
    "/{scan_id}",
    response_model=ScanResponse,
    summary="Get scan details",
    dependencies=[Depends(require_viewer)],
)
async def get_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ScanResponse:
    """Get a specific scan with severity counts."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await scan_service.get_scan_by_id(db, project_id, scan_id, user_id, user_role)


@router.post(
    "/{scan_id}/cancel",
    response_model=ScanResponse,
    summary="Cancel a running scan",
    dependencies=[Depends(require_analyst)],
)
async def cancel_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ScanResponse:
    """Cancel a running or pending scan. Revokes Celery task."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await scan_service.cancel_scan(db, project_id, scan_id, user_id, user_role)


@router.delete(
    "/{scan_id}",
    response_model=MessageResponse,
    summary="Delete scan and its findings",
    dependencies=[Depends(require_analyst)],
)
async def delete_scan(
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> MessageResponse:
    """Delete a scan and all associated findings."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    await scan_service.delete_scan(db, project_id, scan_id, user_id, user_role)
    return MessageResponse(message=f"Scan {scan_id} deleted successfully")

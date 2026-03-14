"""
Reports API — report generation within a project.

Reports are generated asynchronously via Celery.
POST returns a PENDING report record immediately;
poll GET to check status, then download when COMPLETED.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload, require_analyst, require_viewer
from app.models.report import ReportStatus
from app.services import report_service
from app.schemas.report import ReportCreate, ReportResponse
from app.schemas.base import MessageResponse
from fastapi import HTTPException, status

router = APIRouter()


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=201,
    summary="Generate a report",
    dependencies=[Depends(require_analyst)],
)
async def create_report(
    project_id: uuid.UUID,
    body: ReportCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ReportResponse:
    """
    Request report generation (async via Celery).

    Returns immediately with status=PENDING.
    Poll GET /{report_id} to check completion.
    """
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await report_service.create_report(db, project_id, body, user_id, user_role)


@router.get(
    "/",
    response_model=list[ReportResponse],
    summary="List project reports",
    dependencies=[Depends(require_viewer)],
)
async def list_reports(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> list:
    """List reports in a project, newest first."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    reports, _ = await report_service.list_reports(
        db, project_id, user_id, user_role, page=page, page_size=page_size
    )
    return reports


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report details",
    dependencies=[Depends(require_viewer)],
)
async def get_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ReportResponse:
    """Get report status and metadata."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await report_service.get_report_by_id(db, project_id, report_id, user_id, user_role)


@router.get(
    "/{report_id}/download",
    summary="Download generated report file",
    dependencies=[Depends(require_viewer)],
)
async def download_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
):
    """
    Download a completed report file.

    Returns 404 if not completed, 503 if file not found on disk.
    """
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    report = await report_service.get_report_by_id(db, project_id, report_id, user_id, user_role)

    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report is not ready for download (status: {report.status})",
        )

    if not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report file path not set — generation may have failed",
        )

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Report file not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )

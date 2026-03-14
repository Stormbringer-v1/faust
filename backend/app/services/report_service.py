"""
Report service — management of report generation lifecycle.

Reports are generated async via Celery. This service creates the DB record
and dispatches the task; the worker updates status when done.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportStatus
from app.schemas.report import ReportCreate
from app.services.project_service import get_project_by_id


async def get_report_by_id(
    db: AsyncSession,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> Report:
    """
    Fetch a report by ID within a project.

    Raises:
        HTTPException 404 if not found.
    """
    await get_project_by_id(db, project_id, user_id, user_role)

    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.project_id == project_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found in project {project_id}",
        )
    return report


async def list_reports(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Report], int]:
    """List reports for a project with pagination."""
    await get_project_by_id(db, project_id, user_id, user_role)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Report).where(Report.project_id == project_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Report)
        .where(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_report(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ReportCreate,
    generator_id: uuid.UUID,
    user_role: str,
) -> Report:
    """
    Create a Report record and queue its generation.

    Returns the record immediately with status=PENDING.
    The Celery worker will update status to GENERATING -> COMPLETED/FAILED.
    """
    await get_project_by_id(db, project_id, generator_id, user_role)

    report = Report(
        project_id=project_id,
        generated_by=generator_id,
        title=data.title,
        report_format=data.report_format,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    # Dispatch Celery task
    try:
        from app.services.celery_app import dispatch_report_task
        dispatch_report_task(str(report.id))
    except ImportError:
        pass

    return report

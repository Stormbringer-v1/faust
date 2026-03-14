"""
Project service — CRUD for Project model.

Multi-tenancy rule: admins see all projects; analysts/viewers see only projects they own.
CIDR validation for allowed_targets is enforced on write.
"""

import ipaddress
import uuid

from fastapi import HTTPException, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserRole
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def _validate_cidr_list(targets: list[str]) -> None:
    """
    Validate that all entries in targets are valid CIDR/IP notations.

    Raises:
        HTTPException 422 if any entry is invalid.
    """
    for target in targets:
        try:
            ipaddress.ip_network(target, strict=False)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid CIDR/IP target: {target!r}. "
                       "Must be a valid IPv4/IPv6 CIDR (e.g. '192.168.1.0/24') or address.",
            )


async def get_project_by_id(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> Project:
    """
    Fetch a project by ID, enforcing ownership for non-admins.

    Raises:
        HTTPException 404 if not found or not accessible.
    """
    stmt = select(Project).where(Project.id == project_id)
    if user_role != UserRole.ADMIN.value:
        stmt = stmt.where(Project.owner_id == user_id)

    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


async def list_projects(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_role: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Project], int]:
    """
    List projects accessible to the requesting user.

    Admins see all projects; others see only their own.

    Returns:
        Tuple of (projects list, total count).
    """
    offset = (page - 1) * page_size

    stmt = select(Project)
    count_stmt = select(func.count()).select_from(Project)

    if user_role != UserRole.ADMIN.value:
        stmt = stmt.where(Project.owner_id == user_id)
        count_stmt = count_stmt.where(Project.owner_id == user_id)

    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    result = await db.execute(
        stmt.order_by(Project.created_at.desc()).offset(offset).limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_project(
    db: AsyncSession,
    data: ProjectCreate,
    owner_id: uuid.UUID,
) -> Project:
    """
    Create a new project for the given owner.

    Validates CIDR targets if provided.
    """
    if data.allowed_targets:
        _validate_cidr_list(data.allowed_targets)

    project = Project(
        name=data.name,
        description=data.description,
        owner_id=owner_id,
        allowed_targets=data.allowed_targets,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    user_id: uuid.UUID,
    user_role: str,
) -> Project:
    """
    Update mutable project fields.

    Raises:
        HTTPException 404 if not found or not accessible.
    """
    project = await get_project_by_id(db, project_id, user_id, user_role)

    if data.allowed_targets is not None:
        _validate_cidr_list(data.allowed_targets)
        project.allowed_targets = data.allowed_targets

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> None:
    """
    Delete a project (cascades to assets, scans, findings, reports).

    Raises:
        HTTPException 404 if not found or not accessible.
    """
    project = await get_project_by_id(db, project_id, user_id, user_role)
    await db.delete(project)
    await db.flush()

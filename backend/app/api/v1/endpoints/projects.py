"""
Projects API — project CRUD endpoints.

Multi-tenant: admins see all projects; analysts/viewers see only their own.
Owner is set from the JWT payload — never from the request body.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload, require_analyst, require_viewer
from app.services import project_service
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.base import MessageResponse

router = APIRouter()


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=201,
    summary="Create a new project",
    dependencies=[Depends(require_analyst)],
)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ProjectResponse:
    """Create a project. Analyst+ role required. Owner is the requesting user."""
    owner_id = uuid.UUID(payload["sub"])
    return await project_service.create_project(db, body, owner_id)


@router.get(
    "/",
    response_model=list[ProjectResponse],
    summary="List projects",
    dependencies=[Depends(require_viewer)],
)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> list:
    """List projects accessible to the current user."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    projects, _ = await project_service.list_projects(
        db, user_id=user_id, user_role=user_role, page=page, page_size=page_size
    )
    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
    dependencies=[Depends(require_viewer)],
)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ProjectResponse:
    """Get a specific project."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await project_service.get_project_by_id(db, project_id, user_id, user_role)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    dependencies=[Depends(require_analyst)],
)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> ProjectResponse:
    """Update a project. Analyst+ role required."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await project_service.update_project(db, project_id, body, user_id, user_role)


@router.delete(
    "/{project_id}",
    response_model=MessageResponse,
    summary="Delete project",
    dependencies=[Depends(require_analyst)],
)
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> MessageResponse:
    """Delete a project and all associated data (cascade). Analyst+ required."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    await project_service.delete_project(db, project_id, user_id, user_role)
    return MessageResponse(message=f"Project {project_id} deleted successfully")

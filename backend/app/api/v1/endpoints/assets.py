"""
Assets API — asset CRUD within a project.

Scoped under /projects/{project_id}/assets.
All operations verify project access before executing.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload, require_analyst, require_viewer
from app.services import asset_service
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.schemas.base import MessageResponse

router = APIRouter()


@router.post(
    "/",
    response_model=AssetResponse,
    status_code=201,
    summary="Add asset to project",
    dependencies=[Depends(require_analyst)],
)
async def create_asset(
    project_id: uuid.UUID,
    body: AssetCreate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> AssetResponse:
    """Add an asset to a project. Analyst+ required."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await asset_service.create_asset(db, project_id, body, user_id, user_role)


@router.get(
    "/",
    response_model=list[AssetResponse],
    summary="List project assets",
    dependencies=[Depends(require_viewer)],
)
async def list_assets(
    project_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> list:
    """List assets in a project with pagination."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    assets, _ = await asset_service.list_assets(
        db, project_id, user_id, user_role, page=page, page_size=page_size
    )
    return assets


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Get asset details",
    dependencies=[Depends(require_viewer)],
)
async def get_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> AssetResponse:
    """Get a specific asset."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await asset_service.get_asset_by_id(db, project_id, asset_id, user_id, user_role)


@router.patch(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="Update asset",
    dependencies=[Depends(require_analyst)],
)
async def update_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> AssetResponse:
    """Update an asset. Analyst+ required."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await asset_service.update_asset(db, project_id, asset_id, body, user_id, user_role)


@router.delete(
    "/{asset_id}",
    response_model=MessageResponse,
    summary="Delete asset",
    dependencies=[Depends(require_analyst)],
)
async def delete_asset(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> MessageResponse:
    """Delete an asset and its findings. Analyst+ required."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    await asset_service.delete_asset(db, project_id, asset_id, user_id, user_role)
    return MessageResponse(message=f"Asset {asset_id} deleted successfully")

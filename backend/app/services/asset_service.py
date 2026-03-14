"""
Asset service — CRUD for Asset model.

Assets are scoped to a project; all operations verify project membership first.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.project_service import get_project_by_id


async def _check_project_access(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> None:
    """Assert the user can access the project (raises 404 otherwise)."""
    await get_project_by_id(db, project_id, user_id, user_role)


async def get_asset_by_id(
    db: AsyncSession,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> Asset:
    """
    Fetch an asset by ID within a project.

    Raises:
        HTTPException 404 if project not accessible or asset not found.
    """
    await _check_project_access(db, project_id, user_id, user_role)

    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.project_id == project_id)
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found in project {project_id}",
        )
    return asset


async def list_assets(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Asset], int]:
    """
    List assets in a project with pagination.

    Returns:
        Tuple of (assets list, total count).
    """
    await _check_project_access(db, project_id, user_id, user_role)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(Asset).where(Asset.project_id == project_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Asset)
        .where(Asset.project_id == project_id)
        .order_by(Asset.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def create_asset(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: AssetCreate,
    user_id: uuid.UUID,
    user_role: str,
) -> Asset:
    """
    Create an asset within a project.

    Raises:
        HTTPException 409 if the identifier already exists in this project.
    """
    await _check_project_access(db, project_id, user_id, user_role)

    # Check uniqueness
    existing = await db.execute(
        select(Asset).where(
            Asset.project_id == project_id,
            Asset.identifier == data.identifier,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset with identifier '{data.identifier}' already exists in this project",
        )

    import json
    asset = Asset(
        project_id=project_id,
        asset_type=data.asset_type,
        identifier=data.identifier,
        hostname=data.hostname,
        ip_address=data.ip_address,
        tags=json.dumps(data.tags) if data.tags else None,
        notes=data.notes,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


async def update_asset(
    db: AsyncSession,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    data: AssetUpdate,
    user_id: uuid.UUID,
    user_role: str,
) -> Asset:
    """Update mutable fields on an asset."""
    import json
    asset = await get_asset_by_id(db, project_id, asset_id, user_id, user_role)

    if data.hostname is not None:
        asset.hostname = data.hostname
    if data.ip_address is not None:
        asset.ip_address = data.ip_address
    if data.tags is not None:
        asset.tags = json.dumps(data.tags)
    if data.notes is not None:
        asset.notes = data.notes

    await db.flush()
    await db.refresh(asset)
    return asset


async def delete_asset(
    db: AsyncSession,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    user_id: uuid.UUID,
    user_role: str,
) -> None:
    """Delete an asset and cascade to its findings."""
    asset = await get_asset_by_id(db, project_id, asset_id, user_id, user_role)
    await db.delete(asset)
    await db.flush()

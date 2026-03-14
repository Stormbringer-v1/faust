"""
Users API — user management endpoints.

Implemented by BUILDER. Security-audited by ARCHITECT.
All endpoints are admin-only.
"""

import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload, require_admin, UserRole
from app.services import user_service
from app.schemas.user import UserResponse, UserUpdateRole
from app.schemas.base import MessageResponse

router = APIRouter()


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users (admin only)",
    dependencies=[Depends(require_admin)],
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list:
    """List all users with pagination. Admin only."""
    users, _ = await user_service.list_users(db, page=page, page_size=page_size)
    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    dependencies=[Depends(require_admin)],
)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get a specific user. Admin only."""
    return await user_service.get_user_by_id(db, user_id)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role (admin only)",
    dependencies=[Depends(require_admin)],
)
async def update_user_role(
    user_id: uuid.UUID,
    body: UserUpdateRole,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Change a user's role. Admin only."""
    return await user_service.update_user_role(db, user_id, body.role)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Deactivate user (admin only)",
    dependencies=[Depends(require_admin)],
)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Soft-deactivate a user (sets is_active=False). Admin only."""
    user = await user_service.deactivate_user(db, user_id)
    return MessageResponse(message=f"User {user.email} has been deactivated")

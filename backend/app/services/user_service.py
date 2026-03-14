"""
User service — CRUD and management operations for User model.

All DB access is async. Services are thin wrappers that endpoints call;
they contain the query logic and any business rules.
"""

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import UserRole, hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserUpdateRole


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    """
    Fetch a user by primary key.

    Raises:
        HTTPException 404 if not found.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email (returns None if not found)."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[User], int]:
    """
    List all users with pagination.

    Returns:
        Tuple of (users list, total count).
    """
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar_one()

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )
    users = list(result.scalars().all())
    return users, total


async def update_user_role(
    db: AsyncSession,
    user_id: uuid.UUID,
    new_role: UserRole,
) -> User:
    """
    Update a user's role. Admin only.

    Raises:
        HTTPException 404 if user not found.
    """
    user = await get_user_by_id(db, user_id)
    user.role = new_role  # type: ignore[assignment]
    await db.flush()
    await db.refresh(user)
    return user


async def deactivate_user(db: AsyncSession, user_id: uuid.UUID) -> User:
    """
    Soft-deactivate a user (sets is_active=False). Admin only.

    Raises:
        HTTPException 404 if user not found.
        HTTPException 400 if already deactivated.
    """
    user = await get_user_by_id(db, user_id)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already deactivated",
        )
    user.is_active = False
    await db.flush()
    await db.refresh(user)
    return user

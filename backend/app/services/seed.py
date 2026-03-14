"""
Startup seeding — creates the first admin user on fresh deployments.

Reads FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD from settings.
If FIRST_ADMIN_PASSWORD is empty, seeding is skipped (safe default).
Idempotent — safe to call on every startup.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password, UserRole
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


async def seed_first_admin(db: AsyncSession) -> None:
    """
    Create the initial admin user if none exists yet.

    Conditions for seeding:
    - FIRST_ADMIN_PASSWORD is non-empty
    - No user with FIRST_ADMIN_EMAIL already exists
    - No admin-role user exists at all

    This means:
    - Fresh cluster → admin is seeded
    - Existing cluster with admin → noop
    - Password rotation → change FIRST_ADMIN_PASSWORD won't affect existing user
    """
    if not settings.FIRST_ADMIN_PASSWORD:
        logger.debug("FIRST_ADMIN_PASSWORD not set — skipping admin seed")
        return

    # Check if any admin exists
    result = await db.execute(
        select(User).where(User.role == UserRole.ADMIN.value)
    )
    if result.scalar_one_or_none() is not None:
        logger.debug("Admin user already exists — skipping seed")
        return

    # Check if the specific email already exists with a different role
    result = await db.execute(
        select(User).where(User.email == settings.FIRST_ADMIN_EMAIL)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        # Promote to admin instead of creating a duplicate
        existing.role = UserRole.ADMIN  # type: ignore[assignment]
        await db.commit()
        logger.info(
            "Promoted existing user %s to admin role",
            settings.FIRST_ADMIN_EMAIL,
        )
        return

    # Create the admin user
    admin = User(
        email=settings.FIRST_ADMIN_EMAIL,
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        full_name="Faust Administrator",
        role=UserRole.ADMIN,  # type: ignore[assignment]
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    logger.info(
        "✅ First admin user created: %s",
        settings.FIRST_ADMIN_EMAIL,
    )

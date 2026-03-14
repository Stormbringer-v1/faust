"""User schemas — registration, login, and response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.core.security import UserRole
from app.schemas.base import FaustBaseModel


# ── Request schemas ──────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field("", max_length=255)


class UserLogin(BaseModel):
    """Schema for login (separate from OAuth2 form for flexibility)."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None


class UserUpdateRole(BaseModel):
    """Admin-only: change a user's role."""

    role: UserRole


class ChangePassword(BaseModel):
    """Schema for password change (requires current password)."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Response schemas ─────────────────────────────────────────────────

class UserResponse(FaustBaseModel):
    """Public user response — never includes password hash."""

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime


class UserBrief(FaustBaseModel):
    """Minimal user info for embedding in other responses."""

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole

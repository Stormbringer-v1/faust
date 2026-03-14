"""Project schemas — creation, update, and response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import FaustBaseModel


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=2000)
    allowed_targets: list[str] | None = Field(
        None,
        description="CIDR ranges that may be scanned. Null = admin must set later.",
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    allowed_targets: list[str] | None = None


class ProjectResponse(FaustBaseModel):
    """Project response with summary stats."""

    id: uuid.UUID
    name: str
    description: str
    owner_id: uuid.UUID
    allowed_targets: list[str] | None
    created_at: datetime
    updated_at: datetime


class ProjectBrief(FaustBaseModel):
    """Minimal project info for embedding."""

    id: uuid.UUID
    name: str

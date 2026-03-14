"""Asset schemas — creation, update, and response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.asset import AssetType
from app.schemas.base import FaustBaseModel


class AssetCreate(BaseModel):
    """Schema for adding an asset to a project."""

    asset_type: AssetType
    identifier: str = Field(..., min_length=1, max_length=500)
    hostname: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    tags: list[str] | None = None
    notes: str = ""


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""

    hostname: str | None = Field(None, max_length=255)
    ip_address: str | None = Field(None, max_length=45)
    tags: list[str] | None = None
    notes: str | None = None


class AssetResponse(FaustBaseModel):
    """Full asset response."""

    id: uuid.UUID
    project_id: uuid.UUID
    asset_type: AssetType
    identifier: str
    hostname: str | None
    ip_address: str | None
    os_fingerprint: str | None
    open_ports: str | None  # JSON — BUILDER can add a parsed version later
    tags: str | None
    notes: str
    finding_count: int
    created_at: datetime
    updated_at: datetime


class AssetBrief(FaustBaseModel):
    """Minimal asset info for embedding."""

    id: uuid.UUID
    asset_type: AssetType
    identifier: str
    finding_count: int

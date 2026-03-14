"""Scan schemas — creation, status, and response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.scan import ScanStatus, ScanType
from app.schemas.base import FaustBaseModel


class ScanCreate(BaseModel):
    """Schema for launching a new scan."""

    scan_type: ScanType
    targets: list[str] | None = Field(
        None,
        description="Specific targets to scan. If null, scans all project assets.",
    )
    scanner_config: dict | None = Field(
        None,
        description="Scanner-specific configuration options.",
    )


class ScanResponse(FaustBaseModel):
    """Full scan response."""

    id: uuid.UUID
    project_id: uuid.UUID
    initiated_by: uuid.UUID | None
    scan_type: ScanType
    status: ScanStatus
    targets: str | None
    started_at: datetime | None
    completed_at: datetime | None
    finding_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    error_message: str | None
    celery_task_id: str | None
    created_at: datetime
    updated_at: datetime


class ScanBrief(FaustBaseModel):
    """Minimal scan info for embedding."""

    id: uuid.UUID
    scan_type: ScanType
    status: ScanStatus
    finding_count: int
    created_at: datetime


class ScanStatusUpdate(BaseModel):
    """For internal use: update scan status."""

    status: ScanStatus
    error_message: str | None = None

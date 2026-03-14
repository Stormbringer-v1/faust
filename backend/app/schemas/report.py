"""Report schemas — generation request and response."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.report import ReportFormat, ReportStatus
from app.schemas.base import FaustBaseModel


class ReportCreate(BaseModel):
    """Schema for requesting a report generation."""

    title: str = Field(..., min_length=1, max_length=255)
    report_format: ReportFormat = ReportFormat.PDF


class ReportResponse(FaustBaseModel):
    """Full report response."""

    id: uuid.UUID
    project_id: uuid.UUID
    generated_by: uuid.UUID | None
    title: str
    report_format: ReportFormat
    status: ReportStatus
    file_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

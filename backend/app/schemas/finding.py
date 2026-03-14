"""Finding schemas — response and triage."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.finding import FindingSeverity, FindingStatus
from app.schemas.base import FaustBaseModel


class FindingResponse(FaustBaseModel):
    """Full finding response with scoring and AI remediation."""

    id: uuid.UUID
    scan_id: uuid.UUID
    asset_id: uuid.UUID
    title: str
    description: str
    severity: FindingSeverity
    status: FindingStatus
    cve_id: str | None
    cwe_id: str | None
    references: str | None
    cvss_score: float | None
    cvss_vector: str | None
    epss_score: float | None
    epss_percentile: float | None
    is_cisa_kev: bool
    risk_score: float | None
    scanner_name: str | None
    scanner_rule_id: str | None
    evidence: str | None
    ai_remediation: str | None
    ai_provider: str | None
    ai_generated_at: datetime | None
    triaged_by: uuid.UUID | None
    triaged_at: datetime | None
    triage_notes: str | None
    created_at: datetime
    updated_at: datetime


class FindingBrief(FaustBaseModel):
    """Minimal finding for list views and dashboards."""

    id: uuid.UUID
    title: str
    severity: FindingSeverity
    status: FindingStatus
    cve_id: str | None
    risk_score: float | None
    asset_id: uuid.UUID
    created_at: datetime


class FindingTriage(BaseModel):
    """Schema for triaging a finding."""

    status: FindingStatus
    triage_notes: str | None = Field(None, max_length=2000)


class FindingRequestRemediation(BaseModel):
    """Request AI remediation for a finding."""

    provider: str | None = Field(
        None,
        description="AI provider to use. Null = use default.",
    )

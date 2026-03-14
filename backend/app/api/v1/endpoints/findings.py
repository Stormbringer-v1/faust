"""
Findings API — vulnerability findings within a project.

Scoped under /projects/{project_id}/findings.
Findings are created by scanner workers, not via this API.
Triage workflow: open → acknowledged → in_remediation → resolved / false_positive.
"""

import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.remediation.engine import RemediationEngine
from app.core.database import get_db
from app.core.security import get_current_user_payload, require_analyst, require_viewer
from app.models.finding import FindingSeverity, FindingStatus
from app.services import finding_service
from app.schemas.finding import (
    FindingBrief,
    FindingRequestRemediation,
    FindingResponse,
    FindingTriage,
)
from app.schemas.base import MessageResponse

router = APIRouter()


@router.get(
    "/",
    response_model=list[FindingBrief],
    summary="List project findings",
    dependencies=[Depends(require_viewer)],
)
async def list_findings(
    project_id: uuid.UUID,
    severity: FindingSeverity | None = None,
    status: FindingStatus | None = None,
    cve_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> list:
    """
    List findings with optional filters (severity, status, CVE).
    Sorted by risk_score DESC (high-priority first).
    """
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    findings, _ = await finding_service.list_findings(
        db,
        project_id=project_id,
        user_id=user_id,
        user_role=user_role,
        severity=severity,
        finding_status=status,
        cve_id=cve_id,
        page=page,
        page_size=page_size,
    )
    return findings


@router.get(
    "/{finding_id}",
    response_model=FindingResponse,
    summary="Get finding details",
    dependencies=[Depends(require_viewer)],
)
async def get_finding(
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> FindingResponse:
    """Get full finding details including AI remediation and evidence."""
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await finding_service.get_finding_by_id(
        db, project_id, finding_id, user_id, user_role
    )


@router.patch(
    "/{finding_id}/triage",
    response_model=FindingResponse,
    summary="Triage a finding",
    dependencies=[Depends(require_analyst)],
)
async def triage_finding(
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingTriage,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> FindingResponse:
    """
    Update finding triage status.

    Records triaged_by (from JWT) and triaged_at timestamp automatically.
    Valid transitions: open → acknowledged → in_remediation → resolved | false_positive.
    """
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    return await finding_service.triage_finding(
        db, project_id, finding_id, body, user_id, user_role
    )


@router.post(
    "/{finding_id}/remediation",
    response_model=FindingResponse,
    summary="Request AI remediation",
    dependencies=[Depends(require_viewer)],
)
async def request_remediation(
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingRequestRemediation,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(get_current_user_payload),
) -> FindingResponse:
    """
    Generate AI remediation guidance for a finding.

    Uses the configured AI provider (ollama/openai/anthropic/google).
    Result is stored on the finding record and returned immediately.

    Note: For now dispatches a synchronous call; Phase 2 will make this async via Celery.
    """
    user_id = uuid.UUID(payload["sub"])
    user_role = payload["role"]
    finding = await finding_service.get_finding_by_id(
        db, project_id, finding_id, user_id, user_role
    )

    provider_override = body.provider.lower() if body.provider else None
    if provider_override and provider_override not in RemediationEngine.PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown AI provider.",
        )

    engine = RemediationEngine()
    remediation_text = await engine.generate(
        db,
        finding,
        provider_override=provider_override,
    )
    if remediation_text is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI remediation generation failed.",
        )

    await db.flush()
    await db.refresh(finding)
    return finding

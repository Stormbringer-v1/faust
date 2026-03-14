"""
Faust API v1 — aggregated router.

All v1 endpoints are mounted here and included in main.py
under the /api/v1 prefix.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    projects,
    assets,
    scans,
    findings,
    reports,
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
api_v1_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_v1_router.include_router(assets.router, prefix="/projects/{project_id}/assets", tags=["assets"])
api_v1_router.include_router(scans.router, prefix="/projects/{project_id}/scans", tags=["scans"])
api_v1_router.include_router(findings.router, prefix="/projects/{project_id}/findings", tags=["findings"])
api_v1_router.include_router(reports.router, prefix="/projects/{project_id}/reports", tags=["reports"])

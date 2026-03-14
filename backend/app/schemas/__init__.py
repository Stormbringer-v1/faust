"""Faust API schemas — all Pydantic request/response models."""

from app.schemas.base import FaustBaseModel, MessageResponse, PaginatedResponse
from app.schemas.token import RefreshTokenRequest, TokenPair, TokenPayload
from app.schemas.user import (
    ChangePassword,
    UserBrief,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserUpdateRole,
)
from app.schemas.project import ProjectBrief, ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.asset import AssetBrief, AssetCreate, AssetResponse, AssetUpdate
from app.schemas.scan import ScanBrief, ScanCreate, ScanResponse, ScanStatusUpdate
from app.schemas.finding import (
    FindingBrief,
    FindingRequestRemediation,
    FindingResponse,
    FindingTriage,
)
from app.schemas.report import ReportCreate, ReportResponse
from app.schemas.vulnerability import VulnerabilityBrief, VulnerabilityResponse, VulnerabilitySyncStatus

__all__ = [
    # Base
    "FaustBaseModel",
    "MessageResponse",
    "PaginatedResponse",
    # Token
    "TokenPair",
    "TokenPayload",
    "RefreshTokenRequest",
    # User
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserUpdateRole",
    "ChangePassword",
    "UserResponse",
    "UserBrief",
    # Project
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectBrief",
    # Asset
    "AssetCreate",
    "AssetUpdate",
    "AssetResponse",
    "AssetBrief",
    # Scan
    "ScanCreate",
    "ScanResponse",
    "ScanBrief",
    "ScanStatusUpdate",
    # Finding
    "FindingResponse",
    "FindingBrief",
    "FindingTriage",
    "FindingRequestRemediation",
    # Report
    "ReportCreate",
    "ReportResponse",
    # Vulnerability
    "VulnerabilityResponse",
    "VulnerabilityBrief",
    "VulnerabilitySyncStatus",
]

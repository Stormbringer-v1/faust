"""
Security utilities: JWT tokens, password hashing, and RBAC.

Security decisions:
- bcrypt with cost factor 12 (OWASP minimum recommendation)
- JWT with HS256 — acceptable for single-service; upgrade to RS256 if we add microservices
- Tokens include 'type' claim to prevent access/refresh token confusion
- Role-based access with hierarchical permissions (admin > analyst > viewer)
"""

import enum
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# ── Password hashing ────────────────────────────────────────────────
# Using bcrypt directly instead of passlib — passlib 1.7.4 is
# incompatible with bcrypt >= 4.1 on Python 3.12.
import bcrypt

_BCRYPT_ROUNDS = 12  # OWASP minimum recommendation

# ── OAuth2 scheme ────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
)


# ── Enums ────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


# ── Password functions ──────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt (cost 12)."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── JWT functions ────────────────────────────────────────────────────

def create_access_token(
    subject: str | UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: User ID (UUID as string).
        role: User role string.
        expires_delta: Optional custom expiry. Defaults to JWT_ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str | UUID) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have longer expiry and no role claim —
    role is re-fetched from DB on refresh to pick up permission changes.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        HTTPException 401 if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("sub") is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── RBAC Dependencies ───────────────────────────────────────────────

async def get_current_user_payload(
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """
    FastAPI dependency: decode the bearer token and return the payload.

    Returns dict with keys: sub, role, exp, type, iat.
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


class RoleChecker:
    """
    FastAPI dependency for role-based access control.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_admin)])
        async def admin_only():
            ...
    """

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self, payload: dict = Depends(get_current_user_payload),
    ) -> dict[str, Any]:
        user_role = payload.get("role")
        if user_role not in [r.value for r in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return payload


# Pre-built role checkers (hierarchical: admin > analyst > viewer)
require_admin = RoleChecker([UserRole.ADMIN])
require_analyst = RoleChecker([UserRole.ADMIN, UserRole.ANALYST])
require_viewer = RoleChecker([UserRole.ADMIN, UserRole.ANALYST, UserRole.VIEWER])

"""
Auth endpoints — registration, login, token refresh.

Security-critical: implemented by ARCHITECT.
- Rate limiting should be added by BUILDER (middleware or dependency)
- Passwords validated ≥8 chars at schema level, hashed with bcrypt cost 12
- Login returns access + refresh token pair
- Refresh token does NOT carry role — forces DB re-fetch to pick up role changes
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from app.models.user import User
from app.schemas.token import RefreshTokenRequest, TokenPair
from app.schemas.user import UserCreate, UserResponse
from app.schemas.base import MessageResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Create a new user account.

    - Email must be unique
    - Password is hashed with bcrypt (cost 12)
    - New users default to 'viewer' role
    """
    # Check for existing user
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


from app.core.rate_limit import limiter
from fastapi import Request

@router.post(
    "/login",
    response_model=TokenPair,
    summary="Login and receive JWT tokens",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """
    Authenticate with email + password, receive access + refresh tokens.

    Uses OAuth2 password flow (form_data.username = email).
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        # Intentionally vague error to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return TokenPair(
        access_token=create_access_token(subject=user.id, role=role_str),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh an expired access token",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    The user's current role is re-fetched from the database so that
    role changes take effect immediately on next refresh.
    """
    payload = decode_token(body.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type — expected refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return TokenPair(
        access_token=create_access_token(subject=user.id, role=role_str),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Return the authenticated user's profile."""
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

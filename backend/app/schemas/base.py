"""
Base Pydantic schemas shared across all resources.

Provides common response wrappers and pagination.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FaustBaseModel(BaseModel):
    """Base schema with ORM mode enabled."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(FaustBaseModel):
    """Mixin for created_at/updated_at fields in responses."""

    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""

    items: list  # Overridden by concrete types
    total: int
    page: int
    page_size: int
    pages: int


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
    detail: str | None = None

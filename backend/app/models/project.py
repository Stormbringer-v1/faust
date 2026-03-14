"""
Project model — organizational boundary for scans and assets.

A Project is the top-level container. In a multi-tenant deployment,
each project acts as an isolation boundary for assets, scans, and findings.
Projects have an owner (User) and an optional allowed scan scope (CIDR list).
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Project(UUIDMixin, TimestampMixin, Base):
    """A project groups assets, scans, and findings under one boundary."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Allowed scan targets (CIDR notation).
    # Empty list = no restrictions (dangerous — admin only).
    # Example: ["192.168.1.0/24", "10.0.0.0/8"]
    allowed_targets: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        default=list,
    )

    # ── Relationships ────────────────────────────────────────────────
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="projects",
    )
    assets: Mapped[list["Asset"]] = relationship(
        "Asset",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    scans: Mapped[list["Scan"]] = relationship(
        "Scan",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project {self.name!r} owner={self.owner_id}>"

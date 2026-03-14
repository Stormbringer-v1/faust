"""
Asset model — things we scan.

An asset is any scannable target: a host (IP/hostname), a web application,
a cloud resource, a container image, or a network range.
Assets belong to a Project and are linked to Findings.
"""

import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AssetType(str, enum.Enum):
    """Types of scannable assets."""
    HOST = "host"                    # IP address or hostname
    WEB_APP = "web_app"              # URL of a web application
    CLOUD_RESOURCE = "cloud_resource" # AWS/GCP/Azure resource ARN
    CONTAINER = "container"          # Container image reference
    NETWORK = "network"              # CIDR range


class Asset(UUIDMixin, TimestampMixin, Base):
    """A scannable target within a project."""

    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("project_id", "identifier", name="uq_project_asset"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_type: Mapped[AssetType] = mapped_column(
        String(30),
        nullable=False,
    )
    identifier: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Primary identifier: IP, hostname, URL, ARN, or CIDR",
    )
    hostname: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )
    os_fingerprint: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    open_ports: Mapped[str | None] = mapped_column(
        Text,  # JSON array of port objects
        nullable=True,
    )
    tags: Mapped[str | None] = mapped_column(
        Text,  # JSON array of tag strings
        nullable=True,
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    finding_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Denormalized count — updated by scan processor",
    )

    # ── Relationships ────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="assets",
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="asset",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Asset {self.asset_type.value}:{self.identifier}>"

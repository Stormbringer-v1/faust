"""
Scan model — represents a scanning job.

A scan is launched against a project's assets, runs one or more scanner engines,
and produces findings. Scans are executed as Celery tasks with timeouts.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ScanType(str, enum.Enum):
    """Types of scans Faust can run."""
    NETWORK = "network"       # Nmap-based host/port discovery
    WEB_APP = "web_app"       # Nuclei + custom DAST
    CLOUD = "cloud"           # Trivy cloud misconfiguration
    CONTAINER = "container"   # Trivy container image scan
    FULL = "full"             # All applicable scanners


class ScanStatus(str, enum.Enum):
    """Lifecycle states of a scan."""
    PENDING = "pending"       # Queued, waiting for worker
    RUNNING = "running"       # Actively scanning
    COMPLETED = "completed"   # Finished successfully
    FAILED = "failed"         # Scanner error or timeout
    CANCELLED = "cancelled"   # User-cancelled


class Scan(UUIDMixin, TimestampMixin, Base):
    """A scanning job belonging to a project."""

    __tablename__ = "scans"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scan_type: Mapped[ScanType] = mapped_column(
        String(20),
        nullable=False,
    )
    status: Mapped[ScanStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ScanStatus.PENDING,
    )

    # Targets for this scan (subset of project assets or ad-hoc targets)
    targets: Mapped[str | None] = mapped_column(
        Text,  # JSON array of target strings
        nullable=True,
        doc="JSON array of scan targets — validated against project.allowed_targets",
    )

    # Scanner configuration
    scanner_config: Mapped[str | None] = mapped_column(
        Text,  # JSON object with scanner-specific options
        nullable=True,
    )

    # Timing
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Results summary (denormalized for dashboard)
    finding_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    info_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Error details (if status == FAILED)
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Celery task ID for tracking
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="scans",
    )
    initiator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[initiated_by],
    )
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="scan",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Scan {self.scan_type.value} status={self.status.value}>"

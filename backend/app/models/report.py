"""
Report model — generated vulnerability reports.

Reports are generated from project data and can be exported as
PDF, HTML, JSON, or CSV. They capture a point-in-time snapshot
of the vulnerability landscape.
"""

import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ReportFormat(str, enum.Enum):
    """Supported report output formats."""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class ReportStatus(str, enum.Enum):
    """Report generation states."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(UUIDMixin, TimestampMixin, Base):
    """A generated vulnerability report for a project."""

    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    generated_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    report_format: Mapped[ReportFormat] = mapped_column(
        String(10),
        nullable=False,
        default=ReportFormat.PDF,
    )
    status: Mapped[ReportStatus] = mapped_column(
        String(20),
        nullable=False,
        default=ReportStatus.PENDING,
    )
    # Summary statistics snapshot
    summary_json: Mapped[str | None] = mapped_column(
        Text,  # JSON object with severity counts, top CVEs, etc.
        nullable=True,
    )
    # File path or S3 key for the generated report
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="reports",
    )
    generator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[generated_by],
    )

    def __repr__(self) -> str:
        return f"<Report {self.title!r} format={self.report_format.value}>"

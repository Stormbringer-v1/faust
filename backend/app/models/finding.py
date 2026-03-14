"""
Finding model — a discovered vulnerability or misconfiguration.

Findings are produced by scans and linked to both an asset and a scan.
They carry CVE/CWE references, severity scoring (CVSS + EPSS + CISA KEV),
and AI-generated remediation guidance.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class FindingSeverity(str, enum.Enum):
    """CVSS-aligned severity levels."""
    CRITICAL = "critical"  # CVSS 9.0-10.0
    HIGH = "high"          # CVSS 7.0-8.9
    MEDIUM = "medium"      # CVSS 4.0-6.9
    LOW = "low"            # CVSS 0.1-3.9
    INFO = "info"          # Informational, no CVSS


class FindingStatus(str, enum.Enum):
    """Workflow states for finding triage."""
    OPEN = "open"                    # New, untriaged
    CONFIRMED = "confirmed"          # Analyst verified as real
    FALSE_POSITIVE = "false_positive" # Not a real vulnerability
    RESOLVED = "resolved"            # Fix applied and verified
    ACCEPTED_RISK = "accepted_risk"  # Known risk, accepted by stakeholder


class Finding(UUIDMixin, TimestampMixin, Base):
    """A vulnerability or misconfiguration discovered by a scan."""

    __tablename__ = "findings"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Identity ─────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    status: Mapped[FindingStatus] = mapped_column(
        String(20),
        nullable=False,
        default=FindingStatus.OPEN,
        index=True,
    )

    # ── CVE / CWE / References ──────────────────────────────────────
    cve_id: Mapped[str | None] = mapped_column(
        String(20),  # CVE-YYYY-NNNNN
        nullable=True,
        index=True,
    )
    cwe_id: Mapped[str | None] = mapped_column(
        String(10),  # CWE-NNN
        nullable=True,
    )
    references: Mapped[str | None] = mapped_column(
        Text,  # JSON array of reference URLs
        nullable=True,
    )

    # ── Risk Scoring ─────────────────────────────────────────────────
    cvss_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="CVSS v3.1 base score (0.0–10.0)",
    )
    cvss_vector: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="CVSS v3.1 vector string",
    )
    epss_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="EPSS probability (0.0–1.0) — likelihood of exploitation in 30 days",
    )
    epss_percentile: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    is_cisa_kev: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if CVE is in CISA Known Exploited Vulnerabilities catalog",
    )
    risk_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        doc="Faust composite risk score combining CVSS + EPSS + KEV (0–100)",
    )

    # ── Scanner Details ──────────────────────────────────────────────
    scanner_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Which scanner found this: nmap, nuclei, trivy, dast",
    )
    scanner_rule_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Scanner-specific rule/template ID",
    )
    evidence: Mapped[str | None] = mapped_column(
        Text,  # JSON object with scanner-specific evidence
        nullable=True,
    )
    raw_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── AI Remediation ───────────────────────────────────────────────
    ai_remediation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="AI-generated remediation guidance in Markdown",
    )
    ai_provider: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        doc="Which AI provider generated the remediation",
    )
    ai_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Triage ───────────────────────────────────────────────────────
    triaged_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    triaged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    triage_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────────
    scan: Mapped["Scan"] = relationship(
        "Scan",
        back_populates="findings",
    )
    asset: Mapped["Asset"] = relationship(
        "Asset",
        back_populates="findings",
    )
    triager: Mapped["User"] = relationship(
        "User",
        foreign_keys=[triaged_by],
    )

    def __repr__(self) -> str:
        return f"<Finding {self.severity.value}: {self.title[:50]}>"

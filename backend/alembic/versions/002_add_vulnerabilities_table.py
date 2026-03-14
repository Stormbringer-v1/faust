"""Add vulnerabilities reference table.

Stores cached NVD CVE data enriched with EPSS scores and CISA KEV flags.
Used by the remediation engine and risk scoring logic.

Revision ID: 002
Revises: 001
Create Date: 2026-03-14

"""
from __future__ import annotations

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vulnerabilities",
        # ── UUIDMixin ──────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        ),
        # ── TimestampMixin ─────────────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        # ── CVE Identity ───────────────────────────────────────────────
        sa.Column("cve_id", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        # ── CVSS v3.1 ──────────────────────────────────────────────────
        sa.Column("cvss_v31_score", sa.Float(), nullable=True),
        sa.Column("cvss_v31_vector", sa.String(100), nullable=True),
        sa.Column("cvss_v31_severity", sa.String(10), nullable=True),
        # ── CVSS v4.0 ──────────────────────────────────────────────────
        sa.Column("cvss_v40_score", sa.Float(), nullable=True),
        sa.Column("cvss_v40_vector", sa.String(200), nullable=True),
        # ── CWE / References ───────────────────────────────────────────
        sa.Column("cwe_ids", sa.Text(), nullable=True),
        sa.Column("references", sa.Text(), nullable=True),
        # ── NVD Metadata ───────────────────────────────────────────────
        sa.Column("published_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_modified_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("nvd_status", sa.String(30), nullable=True),
        # ── EPSS ───────────────────────────────────────────────────────
        sa.Column("epss_score", sa.Float(), nullable=True),
        sa.Column("epss_percentile", sa.Float(), nullable=True),
        sa.Column("epss_updated_at", sa.DateTime(timezone=True), nullable=True),
        # ── CISA KEV ───────────────────────────────────────────────────
        sa.Column("is_cisa_kev", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("kev_date_added", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kev_due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kev_ransomware_use", sa.Boolean(), nullable=False, server_default="false"),
        # ── Vendor / Product ───────────────────────────────────────────
        sa.Column("vendor", sa.String(200), nullable=True),
        sa.Column("product", sa.String(200), nullable=True),
    )

    # ── Constraints & Indexes ──────────────────────────────────────────
    op.create_unique_constraint(
        "uq_vulnerabilities_cve_id",
        "vulnerabilities",
        ["cve_id"],
    )
    op.create_index(
        "ix_vulnerabilities_cve_id",
        "vulnerabilities",
        ["cve_id"],
    )
    op.create_index(
        "ix_vulnerabilities_epss",
        "vulnerabilities",
        ["epss_score"],
        postgresql_nulls_distinct=True,
    )
    op.create_index(
        "ix_vulnerabilities_kev",
        "vulnerabilities",
        ["is_cisa_kev"],
    )


def downgrade() -> None:
    op.drop_index("ix_vulnerabilities_kev", table_name="vulnerabilities")
    op.drop_index("ix_vulnerabilities_epss", table_name="vulnerabilities")
    op.drop_index("ix_vulnerabilities_cve_id", table_name="vulnerabilities")
    op.drop_constraint("uq_vulnerabilities_cve_id", "vulnerabilities", type_="unique")
    op.drop_table("vulnerabilities")

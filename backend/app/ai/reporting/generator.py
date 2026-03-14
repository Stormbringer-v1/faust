"""
Report rendering engine.

Generates vulnerability assessment reports in multiple formats:
- PDF (via WeasyPrint)
- HTML (via Jinja2 templates)
- JSON (structured data export)
- CSV (spreadsheet-compatible)

Architecture:
- ReportGenerator receives a project_id and report config
- Queries all findings, assets, and scan history for the project
- Renders using format-specific renderer
- Saves output to filesystem (or S3 in future)

BUILDER: implement the render methods.
"""

import csv
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.asset import Asset
from app.models.finding import Finding, FindingSeverity, FindingStatus
from app.models.project import Project
from app.models.report import Report, ReportFormat, ReportStatus
from app.models.scan import Scan

logger = logging.getLogger(__name__)
settings = get_settings()

# Report output directory (inside container)
REPORT_OUTPUT_DIR = Path("/app/reports")


class ReportGenerator:
    """
    Generates vulnerability assessment reports.

    Usage (called from report Celery task):
        generator = ReportGenerator(db)
        file_path = await generator.generate(report_id)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, report_id: uuid.UUID) -> str:
        """
        Generate a report and save to filesystem.

        BUILDER TODO:
        1. Load Report record
        2. Load project with all findings, assets, scans
        3. Build report_data dict (see _build_report_data)
        4. Render using format-specific method:
            - PDF: _render_pdf(report_data) → file_path
            - HTML: _render_html(report_data) → file_path
            - JSON: _render_json(report_data) → file_path
            - CSV: _render_csv(report_data) → file_path
        5. Update Report record with file_path and summary_json
        6. Return file_path

        Returns:
            Path to generated report file.
        """
        result = await self.db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if report is None:
            logger.warning("Report %s not found — skipping", report_id)
            return ""

        report.status = ReportStatus.GENERATING  # type: ignore[assignment]
        await self.db.commit()

        try:
            report_data = await self._build_report_data(report.project_id)

            REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            fmt = report.report_format if isinstance(report.report_format, str) else report.report_format.value
            output_path = REPORT_OUTPUT_DIR / f"report_{report.id}.{fmt}"

            if report.report_format == ReportFormat.PDF:
                file_path = await self._render_pdf(report_data, output_path)
            elif report.report_format == ReportFormat.HTML:
                file_path = await self._render_html(report_data, output_path)
            elif report.report_format == ReportFormat.JSON:
                file_path = await self._render_json(report_data, output_path)
            elif report.report_format == ReportFormat.CSV:
                file_path = await self._render_csv(report_data, output_path)
            else:
                raise ValueError(f"Unsupported report format: {report.report_format}")

            summary_payload = {
                "summary": report_data.get("summary", {}),
                "top_cves": report_data.get("top_cves", []),
            }

            report.file_path = file_path
            report.summary_json = json.dumps(summary_payload, default=str)
            report.status = ReportStatus.COMPLETED  # type: ignore[assignment]
            await self.db.commit()
            return file_path
        except Exception as exc:
            report.status = ReportStatus.FAILED  # type: ignore[assignment]
            report.error_message = str(exc)[:1000]
            await self.db.commit()
            logger.exception("Report %s generation failed: %s", report_id, exc)
            raise

    async def _build_report_data(self, project_id: uuid.UUID) -> dict[str, Any]:
        """
        Query all data needed for a report.

        BUILDER TODO — query and return:
        {
            "project": {name, description, created_at},
            "generated_at": ISO timestamp,
            "summary": {
                "total_findings": int,
                "by_severity": {"critical": N, "high": N, ...},
                "by_status": {"open": N, "resolved": N, ...},
                "total_assets": int,
                "total_scans": int,
            },
            "findings": [
                {
                    "title", "severity", "status", "cve_id", "risk_score",
                    "asset_identifier", "description", "ai_remediation",
                    "scanner_name", "created_at",
                }
            ],
            "assets": [
                {"identifier", "asset_type", "hostname", "finding_count"}
            ],
            "top_cves": [...top 10 CVEs by risk_score],
        }
        """
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if project is None:
            raise ValueError(f"Project {project_id} not found")

        finding_rows = await self.db.execute(
            select(Finding, Asset)
            .join(Asset, Finding.asset_id == Asset.id)
            .where(Asset.project_id == project_id)
        )

        findings: list[dict[str, Any]] = []
        severity_counts = {sev.value: 0 for sev in FindingSeverity}
        status_counts = {status.value: 0 for status in FindingStatus}

        for finding, asset in finding_rows.all():
            sev_key = finding.severity if isinstance(finding.severity, str) else finding.severity.value
            sta_key = finding.status if isinstance(finding.status, str) else finding.status.value
            severity_counts[sev_key] += 1
            status_counts[sta_key] += 1

            findings.append(
                {
                    "title": finding.title,
                    "severity": sev_key,
                    "status": sta_key,
                    "cve_id": finding.cve_id,
                    "risk_score": finding.risk_score,
                    "asset_identifier": asset.identifier,
                    "description": finding.description,
                    "ai_remediation": finding.ai_remediation,
                    "scanner_name": finding.scanner_name,
                    "created_at": finding.created_at.isoformat(),
                }
            )

        findings.sort(
            key=lambda f: (f["risk_score"] is not None, f["risk_score"]),
            reverse=True,
        )

        asset_rows = await self.db.execute(
            select(Asset).where(Asset.project_id == project_id)
        )
        assets = [
            {
                "identifier": asset.identifier,
                "asset_type": asset.asset_type if isinstance(asset.asset_type, str) else asset.asset_type.value,
                "hostname": asset.hostname,
                "finding_count": asset.finding_count,
            }
            for asset in asset_rows.scalars().all()
        ]

        total_assets = await self.db.execute(
            select(func.count()).select_from(Asset).where(Asset.project_id == project_id)
        )
        total_scans = await self.db.execute(
            select(func.count()).select_from(Scan).where(Scan.project_id == project_id)
        )

        total_findings = len(findings)
        by_severity_pct = {
            sev: (count / total_findings * 100 if total_findings else 0)
            for sev, count in severity_counts.items()
        }

        summary = {
            "total_findings": total_findings,
            "by_severity": severity_counts,
            "by_status": status_counts,
            "by_severity_pct": by_severity_pct,
            "total_assets": total_assets.scalar_one(),
            "total_scans": total_scans.scalar_one(),
        }

        cve_stats: dict[str, dict[str, Any]] = {}
        for finding in findings:
            cve_id = finding.get("cve_id")
            if not cve_id:
                continue
            risk_score = finding.get("risk_score") or 0
            entry = cve_stats.get(cve_id)
            if entry is None:
                cve_stats[cve_id] = {
                    "cve_id": cve_id,
                    "max_risk_score": risk_score,
                    "finding_count": 1,
                }
            else:
                entry["finding_count"] += 1
                if risk_score > entry["max_risk_score"]:
                    entry["max_risk_score"] = risk_score

        top_cves = sorted(
            cve_stats.values(),
            key=lambda e: (e["max_risk_score"], e["finding_count"]),
            reverse=True,
        )[:10]

        return {
            "project": {
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat(),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": summary,
            "findings": findings,
            "assets": assets,
            "top_cves": top_cves,
        }

    async def _render_json(self, report_data: dict[str, Any], output_path: Path) -> str:
        """
        Render report as JSON file.

        Straightforward: json.dumps(report_data) → file.
        """
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report_data, handle, indent=2)
        return str(output_path)

    async def _render_csv(self, report_data: dict[str, Any], output_path: Path) -> str:
        """
        Render report as CSV file.

        Columns: title, severity, status, cve_id, risk_score,
                 asset, scanner, description, remediation, created_at

        Use csv.DictWriter from stdlib.
        """
        fieldnames = [
            "title",
            "severity",
            "status",
            "cve_id",
            "risk_score",
            "asset_identifier",
            "scanner_name",
            "description",
            "ai_remediation",
            "created_at",
        ]
        with output_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for finding in report_data.get("findings", []):
                writer.writerow(
                    {
                        "title": finding.get("title"),
                        "severity": finding.get("severity"),
                        "status": finding.get("status"),
                        "cve_id": finding.get("cve_id"),
                        "risk_score": finding.get("risk_score"),
                        "asset_identifier": finding.get("asset_identifier"),
                        "scanner_name": finding.get("scanner_name"),
                        "description": finding.get("description"),
                        "ai_remediation": finding.get("ai_remediation"),
                        "created_at": finding.get("created_at"),
                    }
                )
        return str(output_path)

    async def _render_html(self, report_data: dict[str, Any], output_path: Path) -> str:
        """
        Render report as HTML file.

        BUILDER TODO:
        1. Create a Jinja2 template at backend/app/templates/report.html
        2. Template should include:
            - Header with project name, date, Faust branding
            - Executive summary (severity breakdown chart)
            - Findings table sorted by risk_score DESC
            - Per-finding detail sections with remediation
        3. Render template with report_data
        4. Write to output_path
        """
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        template_dir = Path(__file__).resolve().parents[2] / "templates"
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        template = env.get_template("report.html")
        rendered = template.render(**report_data)
        output_path.write_text(rendered, encoding="utf-8")
        return str(output_path)

    async def _render_pdf(self, report_data: dict[str, Any], output_path: Path) -> str:
        """
        Render report as PDF via WeasyPrint.

        BUILDER TODO:
        1. First render HTML using _render_html()
        2. Convert HTML → PDF using WeasyPrint:
            from weasyprint import HTML
            HTML(filename=html_path).write_pdf(str(output_path))
        3. Clean up intermediate HTML file
        4. Return PDF path

        WeasyPrint requirement: pip install weasyprint
        System deps: pango, cairo (included in Dockerfile)
        """
        from weasyprint import HTML

        html_path = output_path.with_suffix(".html")
        await self._render_html(report_data, html_path)
        HTML(filename=str(html_path)).write_pdf(str(output_path))
        try:
            html_path.unlink()
        except OSError:
            logger.warning("Failed to remove temporary HTML file %s", html_path)
        return str(output_path)

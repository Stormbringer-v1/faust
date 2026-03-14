"""
Base scanner interface and shared infrastructure.

Architecture:
- BaseScanner: abstract class all scanners implement
- RawFinding: intermediate dataclass for scanner output → DB insertion
- ScannerFactory: selects the right scanner(s) for a ScanType
- _run_subprocess: safe async subprocess execution with timeout

BUILDER responsibilities:
- Implement _emit_finding() DB insertion + dedup logic
- Implement _update_scan_counters() to update denormalized severity counts
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.scan import ScanType

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RawFinding:
    """
    Intermediate representation of a scanner finding before DB insertion.

    Every scanner parser converts its native output into RawFinding instances.
    The BaseScanner._emit_finding() method then converts these to ORM objects.

    BUILDER: when inserting, check for deduplication by:
        (scan_id, asset_identifier, title, scanner_rule_id)
    If a duplicate exists within the same scan, skip insertion.
    """

    title: str
    description: str
    severity: str  # "critical" | "high" | "medium" | "low" | "info"
    asset_identifier: str  # IP, hostname, URL — used to resolve/create Asset

    # Optional enrichment (populated by parser if available)
    cve_id: str | None = None
    cwe_id: str | None = None
    cvss_score: float | None = None
    cvss_vector: str | None = None
    references: list[str] = field(default_factory=list)

    # Scanner metadata
    scanner_name: str = ""
    scanner_rule_id: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    raw_output: str | None = None

    # Network-specific (nmap)
    port: int | None = None
    protocol: str | None = None
    service_name: str | None = None
    service_version: str | None = None

    def to_evidence_json(self) -> str:
        """Serialize evidence dict to JSON string for DB storage."""
        return json.dumps(self.evidence, default=str)

    def to_references_json(self) -> str:
        """Serialize references list to JSON string for DB storage."""
        return json.dumps(self.references)


@dataclass
class SubprocessResult:
    """Result from an async subprocess call."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class BaseScanner(ABC):
    """
    Abstract base class for all Faust scanner plugins.

    Lifecycle:
    1. ScannerFactory creates the appropriate scanner instance
    2. Celery task calls scanner.run(targets, config)
    3. Scanner executes subprocess, parses output, calls _emit_finding()
    4. _emit_finding() creates Finding + Asset records in the DB
    5. After run() returns, Celery task updates scan counters and status

    Subclass contract:
    - Implement scanner_type property
    - Implement scanner_name property (e.g. "nmap", "nuclei", "trivy")
    - Implement run() — execute scan, parse, emit findings
    """

    def __init__(self, db: AsyncSession, scan_id: uuid.UUID, project_id: uuid.UUID):
        self.db = db
        self.scan_id = scan_id
        self.project_id = project_id
        self._findings_emitted: int = 0
        self._severity_counts: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

    @property
    @abstractmethod
    def scanner_type(self) -> ScanType:
        """Return the ScanType enum this scanner handles."""
        ...

    @property
    @abstractmethod
    def scanner_name(self) -> str:
        """Return the scanner name string (e.g. 'nmap', 'nuclei', 'trivy')."""
        ...

    @abstractmethod
    async def run(self, targets: list[str], config: dict[str, Any] | None = None) -> None:
        """
        Execute the scan against provided targets.

        Implementations must:
        1. Build the command-line arguments
        2. Call _run_subprocess() to execute
        3. Parse the output using the appropriate parser
        4. Call _emit_finding() for each discovered vulnerability

        Args:
            targets: List of IPs, hostnames, URLs, or image refs to scan.
            config: Optional scanner-specific configuration overrides.

        Raises:
            ScannerError: On critical scanner failures (binary not found, etc.)
        """
        ...

    async def _run_subprocess(
        self,
        cmd: list[str],
        timeout: int | None = None,
    ) -> SubprocessResult:
        """
        Execute a scanner binary as an async subprocess with timeout.

        Safety:
        - Uses create_subprocess_exec (NOT shell=True) to prevent injection
        - Enforces timeout from settings.SCAN_TIMEOUT_SECONDS
        - Captures stdout and stderr separately
        - Logs command (without sensitive args) for debugging

        Args:
            cmd: Command and arguments as a list (e.g. ["nmap", "-sV", "192.168.1.1"])
            timeout: Override timeout in seconds. Default: settings.SCAN_TIMEOUT_SECONDS

        Returns:
            SubprocessResult with returncode, stdout, stderr, timed_out flag.
        """
        effective_timeout = timeout or settings.SCAN_TIMEOUT_SECONDS
        # Log command safely (first 3 args only to avoid leaking targets in logs)
        cmd_preview = " ".join(cmd[:3]) + (" ..." if len(cmd) > 3 else "")
        logger.info(
            "Scanner subprocess starting: %s (timeout=%ds, scan=%s)",
            cmd_preview,
            effective_timeout,
            self.scan_id,
        )

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=effective_timeout,
            )

            result = SubprocessResult(
                returncode=process.returncode or 0,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
            )

            logger.info(
                "Scanner subprocess finished: rc=%d, stdout=%d bytes, stderr=%d bytes",
                result.returncode,
                len(result.stdout),
                len(result.stderr),
            )
            return result

        except asyncio.TimeoutError:
            logger.error(
                "Scanner subprocess timed out after %ds (scan=%s)",
                effective_timeout,
                self.scan_id,
            )
            if process.returncode is None:
                process.kill()
                await process.wait()
            return SubprocessResult(
                returncode=-1,
                stdout="",
                stderr=f"Process timed out after {effective_timeout}s",
                timed_out=True,
            )

    async def _emit_finding(self, finding: RawFinding) -> None:
        """
        Convert a RawFinding to a Finding ORM object and persist it.

        Steps:
        1. Resolve/create Asset by identifier
        2. Deduplicate within this scan
        3. Enrich from Vulnerability table if CVE present
        4. Compute risk_score
        5. Create Finding and add to session
        """
        import json as _json
        from sqlalchemy import select
        from app.models.asset import Asset, AssetType
        from app.models.finding import Finding, FindingSeverity, FindingStatus
        from app.models.vulnerability import Vulnerability
        from app.core.risk import compute_risk_score

        # ── Step 1: Resolve or create Asset ──────────────────────────
        result = await self.db.execute(
            select(Asset).where(
                Asset.project_id == self.project_id,
                Asset.identifier == finding.asset_identifier,
            )
        )
        asset = result.scalar_one_or_none()

        if asset is None:
            # Infer asset type from identifier
            identifier = finding.asset_identifier
            if identifier.startswith("http://") or identifier.startswith("https://"):
                asset_type = AssetType.WEB_APP
            elif "/" in identifier and not identifier.startswith("/"):
                # container image ref like ubuntu:22.04 or docker.io/library/nginx
                asset_type = AssetType.CONTAINER
            else:
                asset_type = AssetType.HOST  # IP or hostname

            asset = Asset(
                project_id=self.project_id,
                asset_type=asset_type,
                identifier=identifier,
                ip_address=finding.asset_identifier if asset_type == AssetType.HOST else None,
            )
            self.db.add(asset)
            await self.db.flush()  # get asset.id

        # ── Step 2: Deduplication check within this scan ─────────────
        dedup_result = await self.db.execute(
            select(Finding).where(
                Finding.scan_id == self.scan_id,
                Finding.asset_id == asset.id,
                Finding.title == finding.title,
                Finding.scanner_rule_id == finding.scanner_rule_id,
            )
        )
        if dedup_result.scalar_one_or_none() is not None:
            logger.debug(
                "Duplicate finding skipped: %s on %s (scan=%s)",
                finding.title,
                finding.asset_identifier,
                self.scan_id,
            )
            return

        # ── Step 3: CVE enrichment from Vulnerability reference table ─
        epss_score: float | None = None
        epss_percentile: float | None = None
        is_cisa_kev: bool = False
        enriched_cvss: float | None = finding.cvss_score

        if finding.cve_id:
            vuln_result = await self.db.execute(
                select(Vulnerability).where(Vulnerability.cve_id == finding.cve_id)
            )
            vuln = vuln_result.scalar_one_or_none()
            if vuln is not None:
                epss_score = vuln.epss_score
                epss_percentile = vuln.epss_percentile
                is_cisa_kev = vuln.is_cisa_kev
                # Prefer NVD CVSS if scanner didn't provide one
                if enriched_cvss is None:
                    enriched_cvss = vuln.cvss_v31_score

        # ── Step 4: Compute composite risk score ──────────────────────
        risk_score = compute_risk_score(
            cvss_score=enriched_cvss,
            epss_score=epss_score,
            is_cisa_kev=is_cisa_kev,
        )

        # ── Step 5: Map severity string to enum ───────────────────────
        severity_map = {
            "critical": FindingSeverity.CRITICAL,
            "high": FindingSeverity.HIGH,
            "medium": FindingSeverity.MEDIUM,
            "low": FindingSeverity.LOW,
            "info": FindingSeverity.INFO,
        }
        severity = severity_map.get(finding.severity.lower(), FindingSeverity.INFO)

        # ── Step 6: Create and persist the Finding ────────────────────
        db_finding = Finding(
            scan_id=self.scan_id,
            asset_id=asset.id,
            title=finding.title,
            description=finding.description,
            severity=severity,
            status=FindingStatus.OPEN,
            cve_id=finding.cve_id,
            cwe_id=finding.cwe_id,
            cvss_score=enriched_cvss,
            cvss_vector=finding.cvss_vector,
            epss_score=epss_score,
            epss_percentile=epss_percentile,
            is_cisa_kev=is_cisa_kev,
            risk_score=risk_score,
            references=finding.to_references_json(),
            evidence=finding.to_evidence_json(),
            scanner_name=finding.scanner_name,
            scanner_rule_id=finding.scanner_rule_id,
        )
        self.db.add(db_finding)

        # Flush periodically to avoid overly large transactions
        self._findings_emitted += 1
        severity_key = finding.severity.lower()
        if severity_key in self._severity_counts:
            self._severity_counts[severity_key] += 1

        if self._findings_emitted % 50 == 0:
            await self.db.flush()

        logger.debug(
            "Finding persisted [%s risk=%.1f]: %s — %s (scan=%s)",
            finding.severity,
            risk_score,
            finding.title,
            finding.asset_identifier,
            self.scan_id,
        )

    @property
    def findings_emitted(self) -> int:
        """Number of findings emitted during this scan run."""
        return self._findings_emitted

    @property
    def severity_counts(self) -> dict[str, int]:
        """Severity breakdown of emitted findings."""
        return self._severity_counts.copy()


class ScannerFactory:
    """
    Factory that selects and instantiates the appropriate scanner(s) for a scan.

    Mapping:
    - NETWORK   → [NmapScanner]
    - WEB_APP   → [NucleiScanner]
    - CLOUD     → [TrivyScanner]
    - CONTAINER → [TrivyScanner]
    - FULL      → [NmapScanner, NucleiScanner, TrivyScanner]
    """

    @staticmethod
    def create(
        scan_type: ScanType,
        db: AsyncSession,
        scan_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> list[BaseScanner]:
        """
        Create scanner instance(s) for the given scan type.

        Returns a list because FULL scans run multiple scanners sequentially.
        """
        from app.services.scanners.nmap_scanner import NmapScanner
        from app.services.scanners.nuclei_scanner import NucleiScanner
        from app.services.scanners.trivy_scanner import TrivyScanner

        scanner_map: dict[ScanType, list[type[BaseScanner]]] = {
            ScanType.NETWORK: [NmapScanner],
            ScanType.WEB_APP: [NucleiScanner],
            ScanType.CLOUD: [TrivyScanner],
            ScanType.CONTAINER: [TrivyScanner],
            ScanType.FULL: [NmapScanner, NucleiScanner, TrivyScanner],
        }

        scanner_classes = scanner_map.get(scan_type, [])
        if not scanner_classes:
            raise ValueError(f"No scanner registered for scan type: {scan_type}")

        return [cls(db=db, scan_id=scan_id, project_id=project_id) for cls in scanner_classes]


class ScannerError(Exception):
    """Raised when a scanner encounters a fatal error."""

    def __init__(self, scanner_name: str, message: str):
        self.scanner_name = scanner_name
        super().__init__(f"[{scanner_name}] {message}")

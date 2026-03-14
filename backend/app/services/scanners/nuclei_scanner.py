"""
Nuclei web vulnerability scanner integration.

Runs ProjectDiscovery's Nuclei as an async subprocess, parses JSONL output,
and emits findings for web application vulnerabilities.

Binary: settings.NUCLEI_BINARY_PATH (default: /usr/local/bin/nuclei)

Nuclei templates are organized by severity and category. We use Nuclei's
built-in template auto-update mechanism (-update-templates on first run).

Output: JSONL (-jsonl) parsed by NucleiJSONParser.
"""

import logging
import os
from typing import Any

from app.core.config import get_settings
from app.models.scan import ScanType
from app.services.scanners.base import BaseScanner, ScannerError

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Scan profiles ─────────────────────────────────────────────────────
NUCLEI_PROFILES: dict[str, list[str]] = {
    "quick": ["-severity", "critical,high", "-rate-limit", "150", "-bulk-size", "50"],
    "standard": ["-severity", "critical,high,medium", "-rate-limit", "100", "-bulk-size", "25"],
    "thorough": ["-rate-limit", "50", "-bulk-size", "10"],
    "passive": ["-passive"],
}


class NucleiScanner(BaseScanner):
    """
    Web application vulnerability scanner using ProjectDiscovery Nuclei.

    Produces findings for:
    - Known CVEs in web applications
    - Misconfigurations (exposed admin panels, default creds, etc.)
    - Information disclosure (server headers, error pages)
    - OWASP Top 10 vulnerabilities
    """

    @property
    def scanner_type(self) -> ScanType:
        return ScanType.WEB_APP

    @property
    def scanner_name(self) -> str:
        return "nuclei"

    async def run(self, targets: list[str], config: dict[str, Any] | None = None) -> None:
        """
        Execute Nuclei scan against web targets and emit findings.

        Args:
            targets: List of URLs to scan (e.g. ["http://192.168.1.1", "https://app.local"])
            config: Optional overrides:
                - profile: str — scan profile name (default: "standard")
                - templates: list[str] — specific template paths/IDs
                - tags: list[str] — template tags to filter (e.g. ["cve", "owasp"])
                - exclude_tags: list[str] — tags to exclude
                - extra_args: list[str] — additional nuclei flags

        BUILDER TODO:
        1. Build command via _build_command()
        2. Execute via _run_subprocess()
        3. Parse JSONL output via NucleiJSONParser
        4. Emit findings
        """
        config = config or {}
        nuclei_binary = settings.NUCLEI_BINARY_PATH

        if not os.path.isfile(nuclei_binary):
            raise ScannerError("nuclei", f"Binary not found at {nuclei_binary}")

        cmd = self._build_command(nuclei_binary, targets, config)
        result = await self._run_subprocess(cmd)

        if result.timed_out:
            raise ScannerError("nuclei", "Scan timed out")

        if result.returncode not in (0, 1):
            raise ScannerError(
                "nuclei",
                f"Exited with code {result.returncode}: {result.stderr[:500]}",
            )

        await self._parse_and_emit(result.stdout)

        logger.info(
            "Nuclei scan complete: %d findings emitted (scan=%s)",
            self.findings_emitted,
            self.scan_id,
        )

    def _build_command(
        self,
        binary: str,
        targets: list[str],
        config: dict[str, Any],
    ) -> list[str]:
        """Build nuclei command-line arguments."""
        profile_name = config.get("profile", "standard")
        profile_args = NUCLEI_PROFILES.get(profile_name, NUCLEI_PROFILES["standard"])

        cmd = [binary]
        cmd.extend(profile_args)

        # Template filters
        if templates := config.get("templates"):
            cmd.extend(["-t", ",".join(templates)])
        if tags := config.get("tags"):
            cmd.extend(["-tags", ",".join(tags)])
        if exclude_tags := config.get("exclude_tags"):
            cmd.extend(["-exclude-tags", ",".join(exclude_tags)])

        # Extra args
        if extra_args := config.get("extra_args"):
            if isinstance(extra_args, list):
                cmd.extend(str(a) for a in extra_args)

        # JSONL output to stdout
        cmd.append("-jsonl")

        # Disable update checks in CI/scan context
        cmd.append("-disable-update-check")

        # Targets via -target flag (one per target)
        for target in targets:
            cmd.extend(["-target", target])

        return cmd

    async def _parse_and_emit(self, jsonl_output: str) -> None:
        """Parse Nuclei JSONL output and emit findings via NucleiJSONParser."""
        from app.services.scanners.parsers.nuclei_parser import NucleiJSONParser

        parser = NucleiJSONParser(scanner_name=self.scanner_name)
        raw_findings = parser.parse(jsonl_output)

        logger.info(
            "Nuclei parsed %d raw findings (scan=%s)",
            len(raw_findings),
            self.scan_id,
        )

        for raw_finding in raw_findings:
            await self._emit_finding(raw_finding)


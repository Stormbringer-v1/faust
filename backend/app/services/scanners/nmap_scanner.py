"""
Nmap network scanner integration.

Runs nmap as an async subprocess, parses XML output, and emits findings
for open ports, identified services, and known vulnerabilities.

Binary: settings.NMAP_BINARY_PATH (default: /usr/bin/nmap)

Scan profiles (configurable via scanner_config):
- "quick":   -sS -sV --top-ports 100 -T4
- "standard": -sS -sV -sC -O -T3  (default)
- "thorough": -sS -sV -sC -O -A --script vuln -T2
- "stealth":  -sS -T1 --scan-delay 1s

Output: XML (-oX -) parsed by NmapXMLParser.
"""

import logging
import os
import tempfile
from typing import Any

from app.core.config import get_settings
from app.models.scan import ScanType
from app.services.scanners.base import BaseScanner, RawFinding, ScannerError

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Scan profiles ─────────────────────────────────────────────────────
NMAP_PROFILES: dict[str, list[str]] = {
    "quick": ["-sT", "-sV", "--top-ports", "100", "-T4"],
    "standard": ["-sT", "-sV", "-sC", "-T3"],
    "thorough": ["-sT", "-sV", "-sC", "-A", "--script", "vuln", "-T2"],
    "stealth": ["-sT", "-T1", "--scan-delay", "1s"],
}


class NmapScanner(BaseScanner):
    """
    Network vulnerability scanner using Nmap.

    Produces findings for:
    - Open ports with identified services
    - Service version detection (banner grabbing)
    - NSE script results (vuln scripts detect known CVEs)
    - OS fingerprinting results
    """

    @property
    def scanner_type(self) -> ScanType:
        return ScanType.NETWORK

    @property
    def scanner_name(self) -> str:
        return "nmap"

    async def run(self, targets: list[str], config: dict[str, Any] | None = None) -> None:
        """
        Execute nmap scan against targets and emit findings.

        Args:
            targets: List of IPs, CIDR ranges, or hostnames.
            config: Optional overrides:
                - profile: str — scan profile name (default: "standard")
                - extra_args: list[str] — additional nmap flags
                - ports: str — port specification (e.g. "1-1024" or "22,80,443")
                - scripts: list[str] — NSE scripts to run

        BUILDER TODO:
        - This method is architecturally complete. Implement the XML parsing
          call in _parse_and_emit() by using NmapXMLParser.
        """
        config = config or {}
        nmap_binary = settings.NMAP_BINARY_PATH

        # Verify binary exists
        if not os.path.isfile(nmap_binary):
            raise ScannerError("nmap", f"Binary not found at {nmap_binary}")

        # Build command
        cmd = self._build_command(nmap_binary, targets, config)

        # Execute
        result = await self._run_subprocess(cmd)

        if result.timed_out:
            raise ScannerError("nmap", "Scan timed out")

        # nmap returns 0 on success, 1 on some host-down scenarios (still valid)
        if result.returncode not in (0, 1):
            raise ScannerError(
                "nmap",
                f"Exited with code {result.returncode}: {result.stderr[:500]}",
            )

        # Parse XML output and emit findings
        await self._parse_and_emit(result.stdout)

        logger.info(
            "Nmap scan complete: %d findings emitted (scan=%s)",
            self.findings_emitted,
            self.scan_id,
        )

    def _build_command(
        self,
        binary: str,
        targets: list[str],
        config: dict[str, Any],
    ) -> list[str]:
        """
        Build the nmap command-line arguments.

        Safety: targets are validated against project CIDR allowlist
        before reaching this point (in scan_service.create_scan).
        """
        profile_name = config.get("profile", "standard")
        profile_args = NMAP_PROFILES.get(profile_name, NMAP_PROFILES["standard"])

        cmd = [binary]
        cmd.extend(profile_args)

        # Port specification
        if ports := config.get("ports"):
            cmd.extend(["-p", str(ports)])

        # Additional NSE scripts
        if scripts := config.get("scripts"):
            cmd.extend(["--script", ",".join(scripts)])

        # Extra args (must be a list of strings)
        if extra_args := config.get("extra_args"):
            if isinstance(extra_args, list):
                cmd.extend(str(a) for a in extra_args)

        # XML output to stdout
        cmd.extend(["-oX", "-"])

        # Targets go last
        cmd.extend(targets)

        return cmd

    async def _parse_and_emit(self, xml_output: str) -> None:
        """Parse nmap XML output and emit findings via the NmapXMLParser."""
        from app.services.scanners.parsers.nmap_parser import NmapXMLParser

        parser = NmapXMLParser(scanner_name=self.scanner_name)
        raw_findings = parser.parse(xml_output)

        logger.info(
            "Nmap parsed %d raw findings (scan=%s)",
            len(raw_findings),
            self.scan_id,
        )

        for raw_finding in raw_findings:
            await self._emit_finding(raw_finding)

"""
Trivy container and cloud scanner integration.

Runs Aqua Trivy as an async subprocess, parses JSON output, and emits
findings for container image vulnerabilities and cloud misconfigurations.

Binary: settings.TRIVY_BINARY_PATH (default: /usr/local/bin/trivy)

Trivy subcommands:
- `trivy image <image>` — scan container images for known CVEs
- `trivy fs <path>` — scan filesystem for vulnerabilities
- `trivy config <path>` — scan IaC files for misconfigurations

Output: JSON (--format json) parsed by TrivyJSONParser.
"""

import logging
import os
from typing import Any

from app.core.config import get_settings
from app.models.scan import ScanType
from app.services.scanners.base import BaseScanner, ScannerError

logger = logging.getLogger(__name__)
settings = get_settings()


class TrivyScanner(BaseScanner):
    """
    Container and cloud misconfiguration scanner using Aqua Trivy.

    Produces findings for:
    - Known CVEs in container image packages (OS + language deps)
    - IaC misconfigurations (Terraform, Kubernetes, Dockerfile, etc.)
    - License compliance violations
    """

    @property
    def scanner_type(self) -> ScanType:
        return ScanType.CONTAINER

    @property
    def scanner_name(self) -> str:
        return "trivy"

    async def run(self, targets: list[str], config: dict[str, Any] | None = None) -> None:
        """
        Execute Trivy scan against targets and emit findings.

        Args:
            targets: List of container image refs or filesystem paths.
                - Docker images: ["nginx:latest", "myapp:v1.2"]
                - Filesystem: ["/path/to/project"]
            config: Optional overrides:
                - subcommand: str — "image" (default) | "fs" | "config"
                - severity: str — filter (e.g. "CRITICAL,HIGH")
                - ignore_unfixed: bool — skip vulns without a fix (default: False)
                - extra_args: list[str]

        BUILDER TODO:
        1. Build command via _build_command()
        2. Execute via _run_subprocess() — run once per target
        3. Parse JSON output via TrivyJSONParser
        4. Emit findings
        """
        config = config or {}
        trivy_binary = settings.TRIVY_BINARY_PATH

        if not os.path.isfile(trivy_binary):
            raise ScannerError("trivy", f"Binary not found at {trivy_binary}")

        subcommand = config.get("subcommand", "image")

        # Trivy scans one target at a time
        for target in targets:
            cmd = self._build_command(trivy_binary, subcommand, target, config)
            result = await self._run_subprocess(cmd)

            if result.timed_out:
                logger.error("Trivy timed out on target %s", target)
                continue

            if result.returncode not in (0, 1):
                logger.error(
                    "Trivy failed on target %s: rc=%d, stderr=%s",
                    target,
                    result.returncode,
                    result.stderr[:500],
                )
                continue

            await self._parse_and_emit(result.stdout, target)

        logger.info(
            "Trivy scan complete: %d findings emitted (scan=%s)",
            self.findings_emitted,
            self.scan_id,
        )

    def _build_command(
        self,
        binary: str,
        subcommand: str,
        target: str,
        config: dict[str, Any],
    ) -> list[str]:
        """Build trivy command-line arguments."""
        cmd = [binary, subcommand]

        # JSON output
        cmd.extend(["--format", "json"])

        # Severity filter
        if severity := config.get("severity"):
            cmd.extend(["--severity", severity])

        # Ignore unfixed
        if config.get("ignore_unfixed", False):
            cmd.append("--ignore-unfixed")

        # Skip update check (use cached DB)
        cmd.append("--skip-db-update")

        # Extra args
        if extra_args := config.get("extra_args"):
            if isinstance(extra_args, list):
                cmd.extend(str(a) for a in extra_args)

        # Target
        cmd.append(target)

        return cmd

    async def _parse_and_emit(self, json_output: str, target: str) -> None:
        """Parse Trivy JSON output and emit findings via TrivyJSONParser."""
        from app.services.scanners.parsers.trivy_parser import TrivyJSONParser

        parser = TrivyJSONParser(scanner_name=self.scanner_name)
        raw_findings = parser.parse(json_output, target)

        logger.info(
            "Trivy parsed %d raw findings for target %s (scan=%s)",
            len(raw_findings),
            target,
            self.scan_id,
        )

        for raw_finding in raw_findings:
            await self._emit_finding(raw_finding)


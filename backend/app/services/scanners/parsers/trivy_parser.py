"""
Trivy JSON output parser.

Parses Trivy's JSON output (--format json) into RawFinding objects.

See TrivyScanner._parse_and_emit() docstring for the full JSON schema.

BUILDER: implement the parse() method following the architecture below.
"""

import json
import logging
from typing import Any

from app.services.scanners.base import RawFinding

logger = logging.getLogger(__name__)


class TrivyJSONParser:
    """Converts Trivy JSON output into RawFinding objects."""

    def __init__(self, scanner_name: str = "trivy"):
        self.scanner_name = scanner_name

    def parse(self, json_output: str, target: str) -> list[RawFinding]:
        """
        Parse Trivy JSON output into RawFinding objects.

        Args:
            json_output: Raw Trivy JSON string.
            target: The scan target (image ref, file path, or URL).

        Returns:
            List of RawFinding objects.
        """
        findings: list[RawFinding] = []

        if not json_output or not json_output.strip():
            logger.warning("TrivyJSONParser received empty output for target: %s", target)
            return findings

        try:
            data = json.loads(json_output)
        except json.JSONDecodeError as e:
            logger.error("TrivyJSONParser: failed to parse JSON for target %s: %s", target, e)
            return findings

        for result in data.get("Results", []):
            result_target: str = result.get("Target", target)
            result_class: str = result.get("Class", "")

            # ── Vulnerabilities (os-pkgs, lang-pkgs) ──────────────────
            for vuln in result.get("Vulnerabilities", []):
                vuln_id: str = vuln.get("VulnerabilityID", "")
                pkg_name: str = vuln.get("PkgName", "")
                installed: str = vuln.get("InstalledVersion", "")
                fixed: str = vuln.get("FixedVersion", "")
                severity: str = vuln.get("Severity", "UNKNOWN").lower()
                # Map UNKNOWN to info
                if severity == "unknown":
                    severity = "info"
                title: str = vuln.get("Title", f"{vuln_id} in {pkg_name}")
                description: str = vuln.get("Description", "")
                references: list[str] = vuln.get("References", [])

                # Extract best CVSS — prefer NVD source
                cvss_score: float | None = None
                cvss_vector: str | None = None
                cvss_data: dict[str, Any] = vuln.get("CVSS", {})
                # Prefer NVD source, then fall back to any source
                for source_key in ["nvd", *cvss_data.keys()]:
                    source = cvss_data.get(source_key, {})
                    if source:
                        v3_score = source.get("V3Score") or source.get("v3Score")
                        v3_vector = source.get("V3Vector") or source.get("v3Vector")
                        if v3_score is not None:
                            try:
                                cvss_score = float(v3_score)
                                cvss_vector = v3_vector
                            except (ValueError, TypeError):
                                pass
                            break

                findings.append(RawFinding(
                    title=f"{vuln_id} \u2014 {pkg_name} {installed}",
                    description=description or title,
                    severity=severity,
                    asset_identifier=target,
                    cve_id=vuln_id if vuln_id.startswith("CVE-") else None,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    references=references,
                    scanner_name=self.scanner_name,
                    scanner_rule_id=f"trivy:{vuln_id}:{pkg_name}",
                    evidence={
                        "package": pkg_name,
                        "installed_version": installed,
                        "fixed_version": fixed,
                        "result_target": result_target,
                        "class": result_class,
                    },
                ))

            # ── Misconfigurations ──────────────────────────────────────
            for misconf in result.get("Misconfigurations", []):
                misconf_id: str = misconf.get("ID", "")
                misconf_title: str = misconf.get("Title", misconf_id)
                misconf_desc: str = misconf.get("Description", "")
                misconf_severity: str = misconf.get("Severity", "UNKNOWN").lower()
                if misconf_severity == "unknown":
                    misconf_severity = "info"
                misconf_refs: list[str] = misconf.get("References", [])
                resolution: str = misconf.get("Resolution", "")

                findings.append(RawFinding(
                    title=f"Misconfiguration: {misconf_title}",
                    description=f"{misconf_desc}\n\nResolution: {resolution}".strip(),
                    severity=misconf_severity,
                    asset_identifier=target,
                    scanner_name=self.scanner_name,
                    scanner_rule_id=f"trivy:misconf:{misconf_id}",
                    references=misconf_refs,
                    evidence={
                        "misconf_id": misconf_id,
                        "result_target": result_target,
                        "class": result_class,
                        "resolution": resolution,
                    },
                ))

        logger.info(
            "TrivyJSONParser parsed %d findings for target: %s", len(findings), target
        )
        return findings

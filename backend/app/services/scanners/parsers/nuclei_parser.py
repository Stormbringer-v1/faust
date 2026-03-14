"""
Nuclei JSONL output parser.

Parses Nuclei's JSON Lines output (-jsonl flag) into RawFinding objects.

Each line is a JSON object representing one matched template result.
See NucleiScanner._parse_and_emit() docstring for the full JSON schema.

BUILDER: implement the parse() method following the architecture below.
"""

import json
import logging
from typing import Any

from app.services.scanners.base import RawFinding

logger = logging.getLogger(__name__)


class NucleiJSONParser:
    """Converts Nuclei JSONL output into RawFinding objects."""

    def __init__(self, scanner_name: str = "nuclei"):
        self.scanner_name = scanner_name

    def parse(self, jsonl_output: str) -> list[RawFinding]:
        """
        Parse Nuclei JSONL output into RawFinding objects.

        Args:
            jsonl_output: Raw JSONL string (one JSON object per line).

        Returns:
            List of RawFinding objects.
        """
        findings: list[RawFinding] = []

        if not jsonl_output or not jsonl_output.strip():
            logger.warning("NucleiJSONParser received empty output")
            return findings

        for line_num, line in enumerate(jsonl_output.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning("NucleiJSONParser: failed to parse line %d: %s", line_num, e)
                continue

            try:
                template_id: str = obj.get("template-id", "unknown")
                info: dict[str, Any] = obj.get("info", {})
                severity: str = info.get("severity", "info").lower()
                name: str = info.get("name", template_id)
                description: str = info.get("description", "")
                host: str = obj.get("host", "")
                matched_at: str = obj.get("matched-at", host)

                classification: dict[str, Any] = info.get("classification", {})
                # Nuclei returns these as lists
                cve_ids: list[str] = classification.get("cve-id", []) or []
                cwe_ids: list[str] = classification.get("cwe-id", []) or []
                cvss_score_raw = classification.get("cvss-score")
                cvss_vector: str | None = classification.get("cvss-metrics")

                cve_id: str | None = cve_ids[0] if cve_ids else None
                cwe_id: str | None = cwe_ids[0] if cwe_ids else None

                cvss_score: float | None = None
                if cvss_score_raw is not None:
                    try:
                        cvss_score = float(cvss_score_raw)
                    except (ValueError, TypeError):
                        pass

                references: list[str] = info.get("reference", []) or []
                if isinstance(references, str):
                    references = [references]

                # Title includes CVE if present
                title = f"{name} \u2014 {cve_id}" if cve_id else name

                findings.append(RawFinding(
                    title=title,
                    description=description or name,
                    severity=severity,
                    asset_identifier=host,
                    cve_id=cve_id,
                    cwe_id=cwe_id,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    references=references,
                    scanner_name=self.scanner_name,
                    scanner_rule_id=template_id,
                    evidence={
                        "matched_at": matched_at,
                        "curl_command": obj.get("curl-command"),
                        "template_id": template_id,
                    },
                ))

            except Exception as e:
                logger.warning(
                    "NucleiJSONParser: error processing line %d: %s", line_num, e
                )
                continue

        logger.info("NucleiJSONParser parsed %d findings", len(findings))
        return findings

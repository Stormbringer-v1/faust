"""
NVD (National Vulnerability Database) API v2.0 client.

Fetches CVE data from NIST NVD and upserts into the Vulnerability table.

API docs: https://nvd.nist.gov/developers/vulnerabilities

Rate limits:
- Without API key: 5 requests per 30-second window
- With API key:    50 requests per 30-second window

Delta sync strategy:
- On first run: fetch all CVEs modified in last 120 days
- On subsequent runs: fetch CVEs modified since last sync timestamp
- NVD API supports lastModStartDate/lastModEndDate parameters
- Maximum date range per request: 120 days

BUILDER: implement the fetch and upsert methods.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NVD_API_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
DEFAULT_HEADERS = {
    "User-Agent": "FaustVulnSync/0.1 (+https://github.com/faust)",
    "Accept": "application/json",
}


class NVDClient:
    """
    Async client for the NVD CVE API v2.0.

    Usage:
        client = NVDClient()
        cves = await client.fetch_recent(days=7)
        # cves is a list of parsed CVE dicts ready for DB upsert
    """

    def __init__(self) -> None:
        self.api_key: str | None = settings.NVD_API_KEY or None
        self.rate_delay: float = 0.6 if self.api_key else 6.0  # seconds between requests

    async def fetch_recent(self, days: int = 7) -> list[dict[str, Any]]:
        """
        Fetch CVEs modified in the last N days from NVD API v2.0.

        Args:
            days: Number of days to look back for modified CVEs.

        Returns:
            List of parsed CVE dicts ready for DB upsert.
        """
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        # NVD expects format without timezone offset
        start_str = start.strftime("%Y-%m-%dT%H:%M:%S.000")
        end_str = end.strftime("%Y-%m-%dT%H:%M:%S.000")

        results: list[dict[str, Any]] = []
        headers = DEFAULT_HEADERS.copy()
        if self.api_key:
            headers["apiKey"] = self.api_key
        results_per_page = 2000
        start_index = 0

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            while True:
                params: dict[str, Any] = {
                    "lastModStartDate": start_str,
                    "lastModEndDate": end_str,
                    "resultsPerPage": results_per_page,
                    "startIndex": start_index,
                }

                try:
                    response = await client.get(NVD_API_BASE, params=params)
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error("NVD API HTTP error: %s", e)
                    break
                except Exception as e:
                    logger.error("NVD API request failed: %s", e)
                    break

                total = data.get("totalResults", 0)
                vulnerabilities = data.get("vulnerabilities", [])

                for vuln_wrapper in vulnerabilities:
                    cve_data = vuln_wrapper.get("cve", {})
                    if cve_data:
                        parsed = self._parse_cve(cve_data)
                        if parsed.get("cve_id"):
                            results.append(parsed)

                start_index += len(vulnerabilities)
                logger.info(
                    "NVD: fetched %d/%d CVEs (startIndex=%d)",
                    start_index,
                    total,
                    start_index,
                )

                if start_index >= total:
                    break

                # Respect rate limits
                await asyncio.sleep(self.rate_delay)

        logger.info("NVDClient.fetch_recent() returned %d CVEs (%d days)", len(results), days)
        return results

    def _parse_cve(self, cve_data: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a single NVD CVE object into a flat dict for DB upsert.

        Args:
            cve_data: Raw NVD CVE JSON object.

        Returns:
            Flat dict matching Vulnerability model fields.
        """
        cve_id = cve_data.get("id", "")

        # English description
        description = ""
        for desc in cve_data.get("descriptions", []):
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break

        # CVSS v3.1 — prefer Primary source from nvd@nist.gov
        cvss_v31_score: float | None = None
        cvss_v31_vector: str | None = None
        cvss_v31_severity: str | None = None
        metrics_v31 = cve_data.get("metrics", {}).get("cvssMetricV31", [])
        # Sort: Primary first
        metrics_v31.sort(key=lambda m: (0 if m.get("type") == "Primary" else 1))
        for metric in metrics_v31:
            cvss_data = metric.get("cvssData", {})
            cvss_v31_score = cvss_data.get("baseScore")
            cvss_v31_vector = cvss_data.get("vectorString")
            cvss_v31_severity = cvss_data.get("baseSeverity")
            break  # Take first (Primary)

        # CVSS v4.0
        cvss_v40_score: float | None = None
        cvss_v40_vector: str | None = None
        metrics_v40 = cve_data.get("metrics", {}).get("cvssMetricV40", [])
        for metric in metrics_v40:
            cvss_data = metric.get("cvssData", {})
            cvss_v40_score = cvss_data.get("baseScore")
            cvss_v40_vector = cvss_data.get("vectorString")
            break

        # CWEs
        cwe_ids: list[str] = []
        for weakness in cve_data.get("weaknesses", []):
            for desc in weakness.get("description", []):
                val = desc.get("value", "")
                if val and val != "NVD-CWE-Other" and val != "NVD-CWE-noinfo":
                    cwe_ids.append(val)

        # References (URL strings only)
        references: list[str] = [
            ref.get("url", "") for ref in cve_data.get("references", [])
            if ref.get("url")
        ]

        # Dates
        published_str = cve_data.get("published")
        last_modified_str = cve_data.get("lastModified")

        def _parse_nvd_date(s: str | None) -> datetime | None:
            if not s:
                return None
            try:
                # NVD format: "2024-01-15T10:15:00.000"
                return datetime.fromisoformat(s.rstrip("Z")).replace(tzinfo=timezone.utc)
            except ValueError:
                return None

        return {
            "cve_id": cve_id,
            "description": description,
            "cvss_v31_score": cvss_v31_score,
            "cvss_v31_vector": cvss_v31_vector,
            "cvss_v31_severity": cvss_v31_severity.lower() if cvss_v31_severity else None,
            "cvss_v40_score": cvss_v40_score,
            "cvss_v40_vector": cvss_v40_vector,
            "cwe_ids": json.dumps(cwe_ids) if cwe_ids else None,
            "references": json.dumps(references) if references else None,
            "published_date": _parse_nvd_date(published_str),
            "last_modified_date": _parse_nvd_date(last_modified_str),
            "nvd_status": cve_data.get("vulnStatus"),
            "vendor": None,   # CPE parsing left for Phase 3
            "product": None,
            "is_cisa_kev": False,
            "kev_ransomware_use": False,
        }

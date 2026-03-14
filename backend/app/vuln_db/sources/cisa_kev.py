"""
CISA Known Exploited Vulnerabilities (KEV) catalog client.

Downloads the KEV JSON catalog and flags matching CVEs in our database.

Source: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
API:    https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json

Format:
{
    "title": "CISA Known Exploited Vulnerabilities Catalog",
    "catalogVersion": "2024.01.15",
    "dateReleased": "2024-01-15T00:00:00.0000Z",
    "count": 1089,
    "vulnerabilities": [
        {
            "cveID": "CVE-2024-12345",
            "vendorProject": "Apache",
            "product": "Log4j",
            "vulnerabilityName": "Apache Log4j Remote Code Execution",
            "dateAdded": "2021-12-10",
            "shortDescription": "...",
            "requiredAction": "Apply updates per vendor instructions.",
            "dueDate": "2021-12-24",
            "knownRansomwareCampaignUse": "Known"
        }
    ]
}

~1100 entries (~200KB). Full download every time (small enough).

BUILDER: implement the fetch and parse methods.
"""

import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "FaustVulnSync/0.1 (+https://github.com/faust)",
    "Accept": "application/json,text/csv,*/*",
}

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


class CISAKEVClient:
    """
    Client for downloading and parsing the CISA KEV catalog.

    Usage:
        client = CISAKEVClient()
        kev_entries = await client.fetch_catalog()
        # kev_entries is a list of dicts with cveID, dateAdded, dueDate, etc.
    """

    async def fetch_catalog(self) -> list[dict[str, Any]]:
        """
        Download and parse the CISA KEV catalog.

        Returns:
            List of parsed KEV entry dicts.
        """
        logger.info("CISAKEVClient: downloading KEV catalog from %s", CISA_KEV_URL)

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=DEFAULT_HEADERS) as client:
                response = await client.get(CISA_KEV_URL)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.error("CISAKEVClient: download failed: %s", e)
            return []

        entries: list[dict[str, Any]] = []
        for vuln in data.get("vulnerabilities", []):
            try:
                entries.append({
                    "cve_id": vuln["cveID"],
                    "vendor": vuln.get("vendorProject"),
                    "product": vuln.get("product"),
                    "name": vuln.get("vulnerabilityName"),
                    "date_added": self._parse_date(vuln.get("dateAdded")),
                    "due_date": self._parse_date(vuln.get("dueDate")),
                    "description": vuln.get("shortDescription"),
                    "required_action": vuln.get("requiredAction"),
                    "ransomware_use": vuln.get("knownRansomwareCampaignUse") == "Known",
                })
            except (KeyError, TypeError) as e:
                logger.warning("CISAKEVClient: skipping malformed entry: %s", e)
                continue

        logger.info("CISAKEVClient: parsed %d KEV entries", len(entries))
        return entries

    @staticmethod
    def _parse_date(date_str: str | None) -> datetime | None:
        """Parse CISA date format (YYYY-MM-DD) to datetime."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

"""
EPSS (Exploit Prediction Scoring System) data client.

Downloads daily EPSS scores from the FIRST EPSS API and updates
the Vulnerability reference table.

Source: https://www.first.org/epss/
API:    https://epss.cyentia.com/epss_scores-current.csv.gz

Format (CSV, gzipped, ~3MB):
    #model_version:v2024.01.01,score_date:2024-01-15T00:00:00+0000
    cve,epss,percentile
    CVE-2024-12345,0.00043,0.08123
    CVE-2023-44228,0.97565,0.99987
    ...

~250K rows. Updated daily. We download the full file and batch-update.

BUILDER: implement the fetch and parse methods.
"""

import csv
import gzip
import io
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

EPSS_URL = "https://epss.cyentia.com/epss_scores-current.csv.gz"


class EPSSClient:
    """
    Client for downloading and parsing EPSS scores.

    Usage:
        client = EPSSClient()
        scores = await client.fetch_scores()
        # scores is a dict: {cve_id: {"epss": float, "percentile": float}}
    """

    async def fetch_scores(self) -> dict[str, dict[str, float]]:
        """
        Download and parse the current EPSS scores CSV.

        Returns:
            Dict mapping CVE ID → {\"epss\": float, \"percentile\": float}
        """
        logger.info("EPSSClient: downloading EPSS scores from %s", EPSS_URL)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(EPSS_URL)
                response.raise_for_status()
        except Exception as e:
            logger.error("EPSSClient: download failed: %s", e)
            return {}

        try:
            decompressed = gzip.decompress(response.content)
            text = decompressed.decode("utf-8")
        except Exception as e:
            logger.error("EPSSClient: decompression failed: %s", e)
            return {}

        scores: dict[str, dict[str, float]] = {}

        # First line is a comment like: #model_version:v2024.01.01,...
        # csv.DictReader handles the header line (cve,epss,percentile)
        reader = csv.DictReader(
            (line for line in text.splitlines() if not line.startswith("#"))
        )

        for row in reader:
            try:
                cve_id = row["cve"]
                epss = float(row["epss"])
                percentile = float(row["percentile"])
                scores[cve_id] = {"epss": epss, "percentile": percentile}
            except (KeyError, ValueError) as e:
                logger.debug("EPSSClient: skipping malformed row: %s — %s", row, e)
                continue

        logger.info("EPSSClient: parsed %d EPSS scores", len(scores))
        return scores

"""
Vulnerability data sync manager.

Orchestrates syncing from NVD, EPSS, and CISA KEV sources into the
Vulnerability reference table. Also propagates updated scores to
existing Finding records.

Architecture:
- Each source client fetches raw data from upstream
- SyncManager upserts into Vulnerability table (ON CONFLICT UPDATE)
- After sync, propagate EPSS/KEV updates to Finding records that have matching CVEs
- Track sync metadata (last sync time) in Redis for delta sync

BUILDER: implement the sync and propagation methods.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.risk import compute_risk_score
from app.models.finding import Finding
from app.models.vulnerability import Vulnerability
from app.vuln_db.sources.nvd import NVDClient
from app.vuln_db.sources.epss import EPSSClient
from app.vuln_db.sources.cisa_kev import CISAKEVClient

logger = logging.getLogger(__name__)


class SyncManager:
    """
    Coordinates vulnerability data synchronization.

    Usage (called from Celery tasks):
        manager = SyncManager(db)
        stats = await manager.sync_nvd(days=7)
        stats = await manager.sync_epss()
        stats = await manager.sync_cisa_kev()
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_nvd(self, days: int = 7) -> dict[str, Any]:
        """
        Sync CVE data from NVD API and upsert into the Vulnerability table.

        Returns:
            Dict with sync statistics.
        """
        start = time.monotonic()
        client = NVDClient()
        cves = await client.fetch_recent(days=days)

        records_created = 0
        records_updated = 0
        batch_size = 500

        for i in range(0, len(cves), batch_size):
            batch = cves[i:i + batch_size]
            if not batch:
                continue

            stmt = pg_insert(Vulnerability).values(batch)
            stmt = stmt.on_conflict_do_update(
                index_elements=["cve_id"],
                set_={
                    "description": stmt.excluded.description,
                    "cvss_v31_score": stmt.excluded.cvss_v31_score,
                    "cvss_v31_vector": stmt.excluded.cvss_v31_vector,
                    "cvss_v31_severity": stmt.excluded.cvss_v31_severity,
                    "cvss_v40_score": stmt.excluded.cvss_v40_score,
                    "cvss_v40_vector": stmt.excluded.cvss_v40_vector,
                    "cwe_ids": stmt.excluded.cwe_ids,
                    "references": stmt.excluded.references,
                    "published_date": stmt.excluded.published_date,
                    "last_modified_date": stmt.excluded.last_modified_date,
                    "nvd_status": stmt.excluded.nvd_status,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            result = await self.db.execute(stmt)
            # rowcount not easily separable for inserts vs updates with ON CONFLICT
            records_created += result.rowcount

        await self.db.commit()
        duration = time.monotonic() - start

        logger.info(
            "NVD sync: %d CVEs processed in %.1fs",
            len(cves),
            duration,
        )

        return {
            "source": "nvd",
            "records_processed": len(cves),
            "records_created": records_created,
            "records_updated": 0,  # Not separately tracked with upsert
            "duration_seconds": round(duration, 2),
        }

    async def sync_epss(self) -> dict[str, Any]:
        """
        Sync EPSS scores and propagate to findings.

        Returns:
            Dict with sync statistics.
        """
        start = time.monotonic()
        client = EPSSClient()
        scores = await client.fetch_scores()

        if not scores:
            duration = time.monotonic() - start
            return {
                "source": "epss",
                "records_processed": 0,
                "records_created": 0,
                "records_updated": 0,
                "duration_seconds": round(duration, 2),
            }

        # Process in batches
        batch_size = 500
        cve_ids = list(scores.keys())
        records_updated = 0
        now = datetime.now(timezone.utc)

        for i in range(0, len(cve_ids), batch_size):
            batch_cve_ids = cve_ids[i:i + batch_size]

            # Find vulnerabilities in our DB for this batch
            result = await self.db.execute(
                select(Vulnerability.id, Vulnerability.cve_id)
                .where(Vulnerability.cve_id.in_(batch_cve_ids))
            )
            rows = result.all()

            for vuln_id, cve_id in rows:
                score_data = scores[cve_id]
                await self.db.execute(
                    update(Vulnerability)
                    .where(Vulnerability.id == vuln_id)
                    .values(
                        epss_score=score_data["epss"],
                        epss_percentile=score_data["percentile"],
                        epss_updated_at=now,
                    )
                )
                records_updated += 1

        await self.db.commit()

        # Propagate updated scores to findings
        findings_updated = await self._propagate_scores_to_findings()

        duration = time.monotonic() - start
        logger.info(
            "EPSS sync: %d scores downloaded, %d vulns updated, %d findings updated in %.1fs",
            len(scores),
            records_updated,
            findings_updated,
            duration,
        )

        return {
            "source": "epss",
            "records_processed": len(scores),
            "records_created": 0,
            "records_updated": records_updated,
            "duration_seconds": round(duration, 2),
        }

    async def sync_cisa_kev(self) -> dict[str, Any]:
        """
        Sync CISA KEV catalog and flag matching vulnerabilities.

        Returns:
            Dict with sync statistics.
        """
        start = time.monotonic()
        client = CISAKEVClient()
        entries = await client.fetch_catalog()

        if not entries:
            duration = time.monotonic() - start
            return {
                "source": "cisa_kev",
                "records_processed": 0,
                "records_created": 0,
                "records_updated": 0,
                "duration_seconds": round(duration, 2),
            }

        # Step 1: Reset all existing KEV flags
        # (handles CVEs removed from KEV catalog)
        await self.db.execute(
            update(Vulnerability)
            .where(Vulnerability.is_cisa_kev == True)  # noqa: E712
            .values(is_cisa_kev=False, kev_date_added=None, kev_due_date=None)
        )

        # Step 2: Apply KEV flags for current catalog entries
        records_updated = 0
        for entry in entries:
            result = await self.db.execute(
                update(Vulnerability)
                .where(Vulnerability.cve_id == entry["cve_id"])
                .values(
                    is_cisa_kev=True,
                    kev_date_added=entry["date_added"],
                    kev_due_date=entry["due_date"],
                    kev_ransomware_use=entry["ransomware_use"],
                    vendor=entry.get("vendor"),
                    product=entry.get("product"),
                )
            )
            records_updated += result.rowcount

        await self.db.commit()

        # Propagate KEV flags to findings
        findings_updated = await self._propagate_scores_to_findings()

        duration = time.monotonic() - start
        logger.info(
            "CISA KEV sync: %d entries processed, %d vulns flagged, %d findings updated in %.1fs",
            len(entries),
            records_updated,
            findings_updated,
            duration,
        )

        return {
            "source": "cisa_kev",
            "records_processed": len(entries),
            "records_created": 0,
            "records_updated": records_updated,
            "duration_seconds": round(duration, 2),
        }

    async def _propagate_scores_to_findings(self) -> int:
        """
        Propagate EPSS/KEV updates from Vulnerability table to Finding records.

        JOINs findings to vulnerabilities on cve_id and recomputes risk_score.

        Returns:
            Count of updated findings.
        """
        from app.models.finding import Finding

        # Fetch findings with a CVE id joined to the vulnerability table
        result = await self.db.execute(
            select(
                Finding.id,
                Finding.cvss_score,
                Vulnerability.cvss_v31_score,
                Vulnerability.epss_score,
                Vulnerability.epss_percentile,
                Vulnerability.is_cisa_kev,
            )
            .join(Vulnerability, Finding.cve_id == Vulnerability.cve_id)
            .where(Finding.cve_id.isnot(None))
        )
        rows = result.all()

        count = 0
        for finding_id, finding_cvss, vuln_cvss, epss, epss_pct, is_kev in rows:
            effective_cvss = finding_cvss or vuln_cvss
            risk = compute_risk_score(
                cvss_score=effective_cvss,
                epss_score=epss,
                is_cisa_kev=bool(is_kev),
            )
            await self.db.execute(
                update(Finding)
                .where(Finding.id == finding_id)
                .values(
                    epss_score=epss,
                    epss_percentile=epss_pct,
                    is_cisa_kev=bool(is_kev),
                    risk_score=risk,
                )
            )
            count += 1

        await self.db.commit()
        logger.info("Score propagation: updated %d findings", count)
        return count

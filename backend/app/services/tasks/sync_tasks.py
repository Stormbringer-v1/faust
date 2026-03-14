"""
Vulnerability data sync Celery tasks.

These tasks run on Celery Beat schedule (see vuln_db/sync/scheduler.py)
to keep the Vulnerability reference table current with NVD, EPSS, and
CISA KEV data. After syncing, they propagate updated scores to findings.

BUILDER: The task orchestration is complete. Implement the actual
data fetching and DB operations in:
- vuln_db/sources/nvd.py (NVDClient)
- vuln_db/sources/epss.py (EPSSClient)
- vuln_db/sources/cisa_kev.py (CISAKEVClient)
- vuln_db/sync/sync_manager.py (SyncManager)
"""

import asyncio
import logging

from app.services.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="faust.sync.nvd",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="sync",
)
def sync_nvd_cves(self) -> dict:
    """
    Sync CVE data from NVD API (delta sync, last 2 days by default).

    Runs every 6 hours via Celery Beat.
    """

    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.vuln_db.sync.sync_manager import SyncManager

        async with AsyncSessionLocal() as db:
            manager = SyncManager(db)
            stats = await manager.sync_nvd(days=2)
            logger.info(
                "NVD sync complete: %d processed, %d created, %d updated (%.1fs)",
                stats["records_processed"],
                stats["records_created"],
                stats["records_updated"],
                stats["duration_seconds"],
            )
            return stats

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("NVD sync failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="faust.sync.epss",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="sync",
)
def sync_epss_scores(self) -> dict:
    """
    Sync EPSS scores and propagate to findings.

    Runs daily at 06:00 UTC via Celery Beat.
    Downloads the full EPSS dataset (~250K CVEs) and batch-updates
    the Vulnerability table, then propagates scores to Finding records.
    """

    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.vuln_db.sync.sync_manager import SyncManager

        async with AsyncSessionLocal() as db:
            manager = SyncManager(db)
            stats = await manager.sync_epss()
            logger.info(
                "EPSS sync complete: %d processed, %d updated (%.1fs)",
                stats["records_processed"],
                stats["records_updated"],
                stats["duration_seconds"],
            )
            return stats

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("EPSS sync failed: %s", exc)
        raise self.retry(exc=exc)


@celery_app.task(
    name="faust.sync.cisa_kev",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    queue="sync",
)
def sync_cisa_kev(self) -> dict:
    """
    Sync CISA Known Exploited Vulnerabilities catalog.

    Runs every 4 hours via Celery Beat.
    Small dataset (~1100 entries), full download each time.
    Flags matching CVEs and propagates KEV status to findings.
    """

    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.vuln_db.sync.sync_manager import SyncManager

        async with AsyncSessionLocal() as db:
            manager = SyncManager(db)
            stats = await manager.sync_cisa_kev()
            logger.info(
                "CISA KEV sync complete: %d processed, %d updated (%.1fs)",
                stats["records_processed"],
                stats["records_updated"],
                stats["duration_seconds"],
            )
            return stats

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("CISA KEV sync failed: %s", exc)
        raise self.retry(exc=exc)

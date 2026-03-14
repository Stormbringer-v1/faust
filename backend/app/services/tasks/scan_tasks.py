"""
Scan Celery task — orchestrates scanner execution.

This task is dispatched by scan_service.create_scan() and runs in
the Celery worker. It:
1. Loads the Scan record from the DB
2. Creates the appropriate scanner(s) via ScannerFactory
3. Runs each scanner against the scan targets
4. Updates scan status and severity counters
5. Handles errors and retries

BUILDER: the architecture is complete. Implement the _emit_finding()
method in BaseScanner to make findings persist to the DB.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.services.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="faust.scan.run",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="scans",
)
def run_scan(self, scan_id: str) -> dict:
    """
    Execute a scan job.

    Lifecycle:
        PENDING → RUNNING → (scanner execution) → COMPLETED | FAILED

    The task loads the Scan, determines which scanner(s) to use based
    on scan_type, executes them sequentially, and updates the DB.
    """

    async def _run() -> dict:
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from sqlalchemy.pool import NullPool

        from app.core.config import get_settings
        from app.models.scan import Scan, ScanStatus
        from app.services.scanners.base import ScannerFactory, ScannerError

        _settings = get_settings()
        _engine = create_async_engine(_settings.database_url, poolclass=NullPool)
        AsyncSessionLocal = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

        async with AsyncSessionLocal() as db:
            # Load scan record
            result = await db.execute(select(Scan).where(Scan.id == scan_id))
            scan = result.scalar_one_or_none()
            if scan is None:
                logger.warning("Scan %s not found — skipping", scan_id)
                return {"status": "not_found"}

            # Guard: only run PENDING scans
            if scan.status != ScanStatus.PENDING:
                logger.warning(
                    "Scan %s is %s, not PENDING — skipping",
                    scan_id,
                    scan.status.value,
                )
                return {"status": "skipped", "reason": f"status is {scan.status.value}"}

            # Transition to RUNNING
            scan.status = ScanStatus.RUNNING  # type: ignore[assignment]
            scan.started_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                # Parse targets from JSON
                targets: list[str] = []
                if scan.targets:
                    targets = json.loads(scan.targets)

                if not targets:
                    logger.warning("Scan %s has no targets", scan_id)
                    scan.status = ScanStatus.FAILED  # type: ignore[assignment]
                    scan.error_message = "No targets specified"
                    scan.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    return {"status": "failed", "reason": "no targets"}

                # Parse scanner config
                config: dict | None = None
                if scan.scanner_config:
                    config = json.loads(scan.scanner_config)

                # Create scanners for this scan type
                scanners = ScannerFactory.create(
                    scan_type=scan.scan_type,
                    db=db,
                    scan_id=scan.id,
                    project_id=scan.project_id,
                )

                # Run each scanner sequentially
                total_findings = 0
                total_counts: dict[str, int] = {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "info": 0,
                }

                for scanner in scanners:
                    logger.info(
                        "Running %s scanner for scan %s (%d targets)",
                        scanner.scanner_name,
                        scan_id,
                        len(targets),
                    )
                    try:
                        await scanner.run(targets, config)
                    except ScannerError as e:
                        logger.error("Scanner %s failed: %s", scanner.scanner_name, e)
                        # Continue with next scanner (don't abort entire scan)
                        continue

                    total_findings += scanner.findings_emitted
                    for sev, count in scanner.severity_counts.items():
                        total_counts[sev] += count

                # Update scan counters
                scan.finding_count = total_findings
                scan.critical_count = total_counts["critical"]
                scan.high_count = total_counts["high"]
                scan.medium_count = total_counts["medium"]
                scan.low_count = total_counts["low"]
                scan.info_count = total_counts["info"]

                # Mark completed
                scan.status = ScanStatus.COMPLETED  # type: ignore[assignment]
                scan.completed_at = datetime.now(timezone.utc)
                await db.commit()

                logger.info(
                    "Scan %s completed: %d findings (C:%d H:%d M:%d L:%d I:%d)",
                    scan_id,
                    total_findings,
                    total_counts["critical"],
                    total_counts["high"],
                    total_counts["medium"],
                    total_counts["low"],
                    total_counts["info"],
                )

                return {
                    "status": "completed",
                    "scan_id": scan_id,
                    "findings": total_findings,
                    "severity_counts": total_counts,
                }

            except Exception as exc:
                scan.status = ScanStatus.FAILED  # type: ignore[assignment]
                scan.error_message = str(exc)[:1000]
                scan.completed_at = datetime.now(timezone.utc)
                await db.commit()
                raise
            finally:
                await _engine.dispose()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("Scan %s failed: %s", scan_id, exc)
        raise self.retry(exc=exc)

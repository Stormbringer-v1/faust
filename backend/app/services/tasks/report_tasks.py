"""Report Celery tasks — placeholder implementations for BUILDER Phase 2."""

import logging
import uuid
from app.services.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="faust.report.generate",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    queue="reports",
)
def generate_report(self, report_id: str) -> dict:
    """
    Generate a report document.

    Generates report content via ReportGenerator and updates status accordingly.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import NullPool
    from app.core.config import get_settings
    from app.models.report import Report, ReportStatus
    from app.ai.reporting.generator import ReportGenerator

    async def _generate():
        _settings = get_settings()
        _engine = create_async_engine(_settings.database_url, poolclass=NullPool)
        AsyncSessionLocal = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with AsyncSessionLocal() as db:
                generator = ReportGenerator(db)
                file_path = await generator.generate(uuid.UUID(report_id))
                if not file_path:
                    return {"status": "not_found", "report_id": report_id}
                return {"status": "completed", "report_id": report_id, "file_path": file_path}
        finally:
            await _engine.dispose()

    try:
        return asyncio.run(_generate())
    except Exception as exc:
        logger.exception("Report %s failed: %s", report_id, exc)
        raise self.retry(exc=exc)

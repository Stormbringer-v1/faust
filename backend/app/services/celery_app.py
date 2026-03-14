"""
Celery application — task broker configuration.

Workers consume tasks from Redis broker.
All long-running operations (scans, report generation) run here.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "faust",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.services.tasks.scan_tasks",
        "app.services.tasks.report_tasks",
        "app.services.tasks.sync_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker safety
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Result TTL
    result_expires=86400,  # 24 hours
    # Soft time limit before SIGTERM; hard limit before SIGKILL
    task_soft_time_limit=3500,
    task_time_limit=3600,
    # Task routing — separate queues for different workloads
    task_routes={
        "faust.scan.*": {"queue": "scans"},
        "faust.report.*": {"queue": "reports"},
        "faust.sync.*": {"queue": "sync"},
    },
)

# ── Celery Beat schedule (periodic tasks) ─────────────────────────────
from app.vuln_db.sync.scheduler import BEAT_SCHEDULE

celery_app.conf.beat_schedule = BEAT_SCHEDULE


def dispatch_scan_task(scan_id: str) -> str:
    """
    Dispatch the run_scan Celery task.

    Returns:
        Celery task ID string.
    """
    from app.services.tasks.scan_tasks import run_scan
    result = run_scan.apply_async(args=[scan_id], queue="scans")
    return result.id


def revoke_task(task_id: str, terminate: bool = True) -> None:
    """
    Revoke (cancel) a Celery task by ID.

    Args:
        task_id: Celery task UUID.
        terminate: If True, send SIGTERM to the worker processing this task.
    """
    celery_app.control.revoke(task_id, terminate=terminate, signal="SIGTERM")


def dispatch_report_task(report_id: str) -> str:
    """
    Dispatch the generate_report Celery task.

    Returns:
        Celery task ID string.
    """
    from app.services.tasks.report_tasks import generate_report
    result = generate_report.apply_async(args=[report_id], queue="reports")
    return result.id

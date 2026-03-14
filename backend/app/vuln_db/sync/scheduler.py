"""
Celery Beat schedule configuration for vulnerability data sync.

Defines periodic task schedules for NVD, EPSS, and CISA KEV syncs.
Imported by celery_app.py to register the beat schedule.

Schedule:
- NVD sync:      Every 6 hours (delta sync, last 2 days)
- EPSS sync:     Daily at 06:00 UTC (EPSS updates daily)
- CISA KEV sync: Every 4 hours (small dataset, critical data)
"""

from celery.schedules import crontab


BEAT_SCHEDULE = {
    "sync-nvd-cves": {
        "task": "faust.sync.nvd",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "options": {"queue": "sync"},
    },
    "sync-epss-scores": {
        "task": "faust.sync.epss",
        "schedule": crontab(minute=0, hour=6),  # Daily at 06:00 UTC
        "options": {"queue": "sync"},
    },
    "sync-cisa-kev": {
        "task": "faust.sync.cisa_kev",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
        "options": {"queue": "sync"},
    },
}

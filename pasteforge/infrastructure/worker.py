from celery import Celery
from celery.schedules import crontab

from pasteforge.core import loggers  # noqa
from pasteforge.core.config import configs

CELERY_CONFIG = {
    "broker_url": configs.CELERY_BROKER_URL,
    "result_backend": configs.CELERY_RESULT_BACKEND,
    "accept_content": ["application/json"],
    "result_accept_content": ["application/json"],
    "timezone": configs.TIMEZONE,
    "task_time_limit": 90,
    "task_max_retries": 3,
    "task_default_retry_delay": 30,
    "imports": ["pasteforge.tasks"],
}

celery_app = Celery(__name__)
celery_app.conf.update(CELERY_CONFIG)


celery_app.conf.beat_schedule = {
    "cleanup-expired-pastes": {
        "task": "pasteforge.tasks.pastes.delete_expired_pastes",
        "schedule": crontab(minute="*/1"),
    },
    "cleanup-expired-idempotency-records": {
        "task": "pasteforge.tasks.idempotency.delete_expired_records",
        "schedule": crontab(minute="0", hour="*/1"),
    },
}

from celery import Celery

from .config import settings

celery_app = Celery(
    "scheduler_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "check-scheduled-posts": {
            "task": "app.tasks.check_scheduled_posts",
            "schedule": 60.0,  # 每分鐘檢查一次
        },
        "cleanup-old-posts": {
            "task": "app.tasks.cleanup_old_posts",
            "schedule": 86400.0,  # 每天清理一次
        },
    },
)

from celery import Celery
from app.config import settings

app = Celery(
    'voice_data_processor',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.celery_tasks']
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
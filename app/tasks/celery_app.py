from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "viralmind",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,       # 10 minutes max per task
    task_soft_time_limit=540,  # soft limit — 9 min
    worker_max_tasks_per_child=50,  # restart worker after 50 tasks (memory leak protection)
)

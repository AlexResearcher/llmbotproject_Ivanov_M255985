from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "bot-service",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=["app.tasks.llm_tasks"],
)

celery_app.conf.update(
    task_default_queue="llm",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)

celery_app.autodiscover_tasks(["app.tasks"])

from app.tasks import llm_tasks  # noqa: F401,E402

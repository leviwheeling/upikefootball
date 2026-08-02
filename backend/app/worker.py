from celery import Celery

from app.config import get_settings

settings = get_settings()
celery_app = Celery("upike_intel", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)


@celery_app.task(name="scraping.healthcheck")  # type: ignore[untyped-decorator]
def worker_healthcheck() -> dict[str, str]:
    return {"status": "ok"}

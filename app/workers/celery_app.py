from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "cr_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="discovery",
    task_queues={
        "discovery": {"exchange": "discovery", "routing_key": "discovery"},
        "probe": {"exchange": "probe", "routing_key": "probe"},
        "fetch": {"exchange": "fetch", "routing_key": "fetch"},
        "normalize": {"exchange": "normalize", "routing_key": "normalize"},
        "extract": {"exchange": "extract", "routing_key": "extract"},
        "score": {"exchange": "score", "routing_key": "score"},
        "reindex": {"exchange": "reindex", "routing_key": "reindex"},
    },
    task_routes={
        "app.workers.tasks.discovery.*": {"queue": "discovery"},
        "app.workers.tasks.probe.*": {"queue": "probe"},
        "app.workers.tasks.fetch.*": {"queue": "fetch"},
        "app.workers.tasks.normalize.*": {"queue": "normalize"},
        "app.workers.tasks.extract.*": {"queue": "extract"},
        "app.workers.tasks.score.*": {"queue": "score"},
        "app.workers.tasks.reindex.*": {"queue": "reindex"},
    },
)

celery_app.autodiscover_tasks(["app.workers.tasks"])

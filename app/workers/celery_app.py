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
        "compile_kb": {"exchange": "compile_kb", "routing_key": "compile_kb"},
        "lint_kb": {"exchange": "lint_kb", "routing_key": "lint_kb"},
        "refresh_backlinks": {"exchange": "refresh_backlinks", "routing_key": "refresh_backlinks"},
        "detect_conflicts": {"exchange": "detect_conflicts", "routing_key": "detect_conflicts"},
        "generate_outputs": {"exchange": "generate_outputs", "routing_key": "generate_outputs"},
        "file_outputs": {"exchange": "file_outputs", "routing_key": "file_outputs"},
        "rebuild_indexes": {"exchange": "rebuild_indexes", "routing_key": "rebuild_indexes"},
    },
    task_routes={
        "app.workers.tasks.discovery.*": {"queue": "discovery"},
        "app.workers.tasks.probe.*": {"queue": "probe"},
        "app.workers.tasks.fetch.*": {"queue": "fetch"},
        "app.workers.tasks.normalize.*": {"queue": "normalize"},
        "app.workers.tasks.extract.*": {"queue": "extract"},
        "app.workers.tasks.score.*": {"queue": "score"},
        "app.workers.tasks.reindex.*": {"queue": "reindex"},
        "app.workers.tasks.kb.compile_document_version": {"queue": "compile_kb"},
        "app.workers.tasks.kb.run_compile_kb": {"queue": "compile_kb"},
        "app.workers.tasks.kb.lint_kb": {"queue": "lint_kb"},
        "app.workers.tasks.kb.refresh_backlinks": {"queue": "refresh_backlinks"},
        "app.workers.tasks.kb.detect_conflicts": {"queue": "detect_conflicts"},
        "app.workers.tasks.kb.generate_outputs": {"queue": "generate_outputs"},
        "app.workers.tasks.kb.file_outputs": {"queue": "file_outputs"},
        "app.workers.tasks.kb.rebuild_indexes": {"queue": "rebuild_indexes"},
    },
)

celery_app.autodiscover_tasks(["app.workers.tasks"])

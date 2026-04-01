from app.workers.celery_app import celery_app
from app.services.normalize import NormalizeService


@celery_app.task(name="app.workers.tasks.normalize.normalize_document", queue="normalize")
def normalize_document(version_id: int):
    service = NormalizeService()
    service.normalize(version_id=version_id)

from app.workers.celery_app import celery_app
from app.services.fetch import FetchService


@celery_app.task(name="app.workers.tasks.fetch.fetch_document", queue="fetch")
def fetch_document(version_id: int):
    service = FetchService()
    service.fetch(version_id=version_id)

from celery import chain

from app.services.normalize import NormalizeService
from app.workers.celery_app import celery_app
from app.workers.tasks.extract import extract_document
from app.workers.tasks.kb import compile_document_version


@celery_app.task(name="app.workers.tasks.normalize.normalize_document", queue="normalize")
def normalize_document(version_id: int):
    service = NormalizeService()
    if service.normalize(version_id=version_id):
        chain(compile_document_version.s(version_id), extract_document.si(version_id)).apply_async()

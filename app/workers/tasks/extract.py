from app.workers.celery_app import celery_app
from app.services.extraction.pipeline import ExtractionPipeline


@celery_app.task(name="app.workers.tasks.extract.extract_document", queue="extract")
def extract_document(version_id: int):
    pipeline = ExtractionPipeline()
    pipeline.extract(version_id=version_id)

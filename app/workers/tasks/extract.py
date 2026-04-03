from app.workers.celery_app import celery_app
from app.services.candidate_engine import CandidateEngine
from app.services.extraction.pipeline import ExtractionPipeline


@celery_app.task(name="app.workers.tasks.extract.extract_document", queue="extract")
def extract_document(version_id: int) -> dict:
    """
    Clinical extraction (TZ §14) + генерация направленных пар PairEvidence (TZ §15.1).
    Очередь extract — см. docker-compose worker -Q.
    """
    pipeline = ExtractionPipeline()
    pipeline.extract(version_id=version_id)
    pairs_created = CandidateEngine().generate_pairs(version_id)
    return {"status": "ok", "version_id": version_id, "candidate_pairs_created": pairs_created}

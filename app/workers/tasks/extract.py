from celery import current_task

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
from app.services.candidate_engine import CandidateEngine
from app.workers.celery_app import celery_app
from app.services.extraction.pipeline import ExtractionPipeline
from app.services.pipeline_event_log import write_pipeline_event


@celery_app.task(name="app.workers.tasks.extract.extract_document", queue="extract")
def extract_document(version_id: int):
    session = get_sync_session()
    version = session.get(DocumentVersion, version_id)
    session.close()
    registry_id = version.registry_id if version else None
    task_id = getattr(getattr(current_task, "request", None), "id", None)
    if registry_id is not None:
        write_pipeline_event(
            document_registry_id=registry_id,
            document_version_id=version_id,
            celery_task_id=task_id,
            stage="extract",
            status="start",
            message="Started extract stage",
            detail_json={"version_id": version_id},
        )
    pipeline = ExtractionPipeline()
    try:
        extraction_result = pipeline.extract(version_id=version_id)
        candidate_pairs_count = CandidateEngine().generate_pairs(version_id=version_id)
        if registry_id is not None:
            write_pipeline_event(
                document_registry_id=registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="extract",
                status="success",
                message="Extract stage finished successfully",
                detail_json={
                    "version_id": version_id,
                    "mnn_count": extraction_result.mnn_count,
                    "uur_udd_count": extraction_result.uur_udd_count,
                    "relation_count": extraction_result.relation_count,
                    "context_count": extraction_result.context_count,
                    "mnn_molecule_ids": list(extraction_result.mnn_molecule_ids),
                    "candidate_pairs_count": candidate_pairs_count,
                },
            )
    except Exception as exc:
        if registry_id is not None:
            write_pipeline_event(
                document_registry_id=registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="extract",
                status="failed",
                message="Extract stage raised an exception",
                detail_json={"reason_code": "extract_exception", "error": str(exc)},
            )
        raise

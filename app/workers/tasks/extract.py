from celery import current_task

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
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
        pipeline.extract(version_id=version_id)
        if registry_id is not None:
            write_pipeline_event(
                document_registry_id=registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="extract",
                status="success",
                message="Extract stage finished successfully",
                detail_json={"version_id": version_id},
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

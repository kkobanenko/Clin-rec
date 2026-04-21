from celery import current_task

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
from app.workers.celery_app import celery_app
from app.services.normalize import NormalizeService
from app.services.pipeline_event_log import write_pipeline_event


@celery_app.task(name="app.workers.tasks.normalize.normalize_document", queue="normalize")
def normalize_document(version_id: int):
    task_id = getattr(getattr(current_task, "request", None), "id", None)
    session = get_sync_session()
    version = session.get(DocumentVersion, version_id)
    session.close()
    registry_id = version.registry_id if version else None
    if registry_id is not None:
        write_pipeline_event(
            document_registry_id=registry_id,
            document_version_id=version_id,
            celery_task_id=task_id,
            stage="normalize",
            status="start",
            message="Started normalize stage",
            detail_json={"version_id": version_id},
        )
    service = NormalizeService()
    result = service.normalize(version_id=version_id)
    if result.document_registry_id is not None:
        write_pipeline_event(
            document_registry_id=result.document_registry_id,
            document_version_id=version_id,
            celery_task_id=task_id,
            stage="normalize",
            status=result.status,
            message=f"Normalize stage finished with status={result.status}",
            detail_json={
                "sections_count": result.sections_count,
                "fragments_count": result.fragments_count,
                "source_used": result.source_used,
                "reason_code": result.reason_code,
                "queued_extract": result.queued_extract,
            },
        )

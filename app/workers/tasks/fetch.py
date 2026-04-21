from celery import current_task

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
from app.workers.celery_app import celery_app
from app.services.fetch import FetchService
from app.services.pipeline_event_log import write_pipeline_event


@celery_app.task(name="app.workers.tasks.fetch.fetch_document", queue="fetch")
def fetch_document(version_id: int):
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
            stage="fetch",
            status="start",
            message="Started fetch stage",
            detail_json={"version_id": version_id},
        )
    service = FetchService()
    try:
        result = service.fetch(version_id=version_id)
        if result.document_registry_id is not None:
            write_pipeline_event(
                document_registry_id=result.document_registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="fetch",
                status=result.status,
                message=f"Fetch stage finished with status={result.status}",
                detail_json={
                    "fetched_artifacts": list(result.fetched_artifacts),
                    "reason_code": result.reason_code,
                    "queued_normalize": result.queued_normalize,
                },
            )
    except Exception as exc:
        if registry_id is not None:
            write_pipeline_event(
                document_registry_id=registry_id,
                document_version_id=version_id,
                celery_task_id=task_id,
                stage="fetch",
                status="failed",
                message="Fetch stage raised an exception",
                detail_json={"reason_code": "fetch_exception", "error": str(exc)},
            )
        raise

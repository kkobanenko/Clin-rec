from celery import chain

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
from app.services.normalize import NormalizeService
from app.services.pipeline_event_log import write_pipeline_event
from app.workers.celery_app import celery_app
from app.workers.tasks.extract import extract_document
from app.workers.tasks.kb import compile_document_version


@celery_app.task(name="app.workers.tasks.normalize.normalize_document", bind=True, queue="normalize")
def normalize_document(self, version_id: int):
    tid = getattr(self.request, "id", None)
    session = get_sync_session()
    try:
        ver = session.get(DocumentVersion, version_id)
        reg_id = ver.registry_id if ver else None
    finally:
        session.close()

    if reg_id is not None:
        write_pipeline_event(
            document_registry_id=reg_id,
            document_version_id=version_id,
            celery_task_id=tid,
            stage="normalize",
            status="started",
            message="normalize started",
            detail_json=None,
        )

    service = NormalizeService()
    try:
        ok = service.normalize(version_id=version_id)
    except Exception as e:
        if reg_id is not None:
            write_pipeline_event(
                document_registry_id=reg_id,
                document_version_id=version_id,
                celery_task_id=tid,
                stage="normalize",
                status="failure",
                message=str(e)[:2000],
                detail_json={"exception_type": type(e).__name__},
            )
        raise

    if ok:
        if reg_id is not None:
            write_pipeline_event(
                document_registry_id=reg_id,
                document_version_id=version_id,
                celery_task_id=tid,
                stage="normalize",
                status="success",
                message="normalize ok; queued compile_kb chain",
                detail_json=None,
            )
        chain(compile_document_version.s(version_id), extract_document.si(version_id)).apply_async()
    else:
        if reg_id is not None:
            write_pipeline_event(
                document_registry_id=reg_id,
                document_version_id=version_id,
                celery_task_id=tid,
                stage="normalize",
                status="failure",
                message="no sections extracted (normalize returned False)",
                detail_json=None,
            )

    return {"ok": ok, "version_id": version_id}

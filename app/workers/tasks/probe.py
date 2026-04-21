from celery import current_task

from app.workers.celery_app import celery_app
from app.services.probe import ProbeService
from app.services.pipeline_event_log import write_pipeline_event


@celery_app.task(name="app.workers.tasks.probe.probe_document", queue="probe")
def probe_document(registry_id: int):
    task_id = getattr(getattr(current_task, "request", None), "id", None)
    write_pipeline_event(
        document_registry_id=registry_id,
        document_version_id=None,
        celery_task_id=task_id,
        stage="probe",
        status="start",
        message="Started probe stage",
        detail_json={"registry_id": registry_id},
    )
    service = ProbeService()
    try:
        result = service.probe(registry_id=registry_id)
        write_pipeline_event(
            document_registry_id=registry_id,
            document_version_id=result.document_version_id,
            celery_task_id=task_id,
            stage="probe",
            status=result.status,
            message=f"Probe stage finished with status={result.status}",
            detail_json={
                "source_primary": result.source_primary,
                "reason_code": result.reason_code,
                "html_reason_code": result.html_reason_code,
                "pdf_reason_code": result.pdf_reason_code,
                "queued_fetch": result.queued_fetch,
            },
        )
    except Exception as exc:
        write_pipeline_event(
            document_registry_id=registry_id,
            document_version_id=None,
            celery_task_id=task_id,
            stage="probe",
            status="failed",
            message="Probe stage raised an exception",
            detail_json={"reason_code": "probe_exception", "error": str(exc)},
        )
        raise

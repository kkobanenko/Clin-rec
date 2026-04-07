from app.services.fetch import FetchService
from app.services.pipeline_event_log import write_pipeline_event
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.fetch.fetch_document", bind=True, queue="fetch")
def fetch_document(self, version_id: int, force: bool = False):
    """
    Celery: скачать сырьё. При отсутствии валидных артефактов — FAILURE, чтобы UI видел ошибку.
    """
    tid = getattr(self.request, "id", None)
    service = FetchService()
    result = service.fetch(version_id=version_id, force=force, celery_task_id=tid)

    if not result.get("ok"):
        err = result.get("error", "fetch_failed")
        rid = result.get("registry_id")
        if rid:
            write_pipeline_event(
                document_registry_id=rid,
                document_version_id=version_id,
                celery_task_id=tid,
                stage="fetch",
                status="failure",
                message=f"fetch aborted: {err}",
                detail_json=result,
            )
        raise RuntimeError(err)

    if not result.get("fetched_any"):
        # Событие failure уже записано в FetchService.fetch
        raise RuntimeError(
            "No valid html/pdf stored after fetch. Check pipeline_event_log, URLs, and worker logs (Playwright/network)."
        )

    return result

from app.workers.celery_app import celery_app
from app.services.probe import ProbeService


@celery_app.task(name="app.workers.tasks.probe.probe_document", queue="probe")
def probe_document(registry_id: int):
    service = ProbeService()
    service.probe(registry_id=registry_id)

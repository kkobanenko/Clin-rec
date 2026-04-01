from app.workers.celery_app import celery_app
from app.services.discovery import DiscoveryService


@celery_app.task(name="app.workers.tasks.discovery.run_full_sync", queue="discovery")
def run_full_sync(run_id: int):
    service = DiscoveryService()
    service.execute(run_id=run_id, mode="full")


@celery_app.task(name="app.workers.tasks.discovery.run_incremental_sync", queue="discovery")
def run_incremental_sync(run_id: int):
    service = DiscoveryService()
    service.execute(run_id=run_id, mode="incremental")

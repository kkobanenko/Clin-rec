"""Запись строк в pipeline_event_log (синхронно, из Celery-воркера)."""

import logging

from app.core.sync_database import get_sync_session
from app.models.pipeline_event import PipelineEventLog

logger = logging.getLogger(__name__)


def write_pipeline_event(
    *,
    document_registry_id: int,
    document_version_id: int | None,
    celery_task_id: str | None,
    stage: str,
    status: str,
    message: str,
    detail_json: dict | None = None,
) -> None:
    session = get_sync_session()
    try:
        row = PipelineEventLog(
            document_registry_id=document_registry_id,
            document_version_id=document_version_id,
            celery_task_id=celery_task_id,
            stage=stage,
            status=status,
            message=message,
            detail_json=detail_json,
        )
        session.add(row)
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("write_pipeline_event failed")
        raise
    finally:
        session.close()

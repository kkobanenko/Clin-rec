"""Синхронные операции с output_release для Celery (создание черновика, output filing)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.sync_database import get_sync_session
from app.models.knowledge import OutputRelease

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "0.1.0"


def create_pending_output(
    output_type: str,
    title: str | None = None,
    scope_json: dict | None = None,
    generator_version: str = GENERATOR_VERSION,
) -> int:
    """Создать строку output_release в статусе ожидания (пока без файла в S3)."""
    session = get_sync_session()
    try:
        safe_title = (title or "").strip() or f"{output_type} draft"
        row = OutputRelease(
            output_type=output_type,
            title=safe_title,
            scope_json=scope_json,
            generator_version=generator_version,
            review_status="pending",
            file_back_status="pending",
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        logger.info("Created output_release id=%s type=%s", row.id, output_type)
        return row.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def apply_file_back(output_id: int, file_back_status: str) -> dict:
    """Обновить статус filing; при accepted проставить released_at и review_status."""
    session = get_sync_session()
    try:
        row = session.get(OutputRelease, output_id)
        if not row:
            logger.warning("output_release %s not found", output_id)
            return {"status": "error", "reason": "output_not_found", "output_id": output_id}

        row.file_back_status = file_back_status
        if file_back_status == "accepted":
            row.released_at = datetime.now(timezone.utc)
            row.review_status = "accepted"
        elif file_back_status == "rejected":
            row.review_status = "rejected"
        else:
            row.review_status = "needs_review"

        session.commit()
        logger.info("file_back output_id=%s status=%s", output_id, file_back_status)
        return {"status": "ok", "output_id": output_id, "file_back_status": file_back_status}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

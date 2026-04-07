"""Журнал событий pipeline по документу (refetch, normalize) для UI и отладки."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PipelineEventLog(Base):
    __tablename__ = "pipeline_event_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    document_registry_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("document_registry.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("document_version.id", ondelete="SET NULL"), nullable=True, index=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    detail_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

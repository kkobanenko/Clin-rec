"""Сбор счётчиков для задачи rebuild_indexes до появления полноценного FTS/BI-слоя."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select

from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.models.knowledge import KnowledgeArtifact
from app.models.text import DocumentSection, TextFragment


def collect_index_stats() -> dict[str, Any]:
    session = get_sync_session()
    try:
        return {
            "status": "ok",
            "document_registry": session.scalar(select(func.count()).select_from(DocumentRegistry)) or 0,
            "document_version": session.scalar(select(func.count()).select_from(DocumentVersion)) or 0,
            "source_artifact": session.scalar(select(func.count()).select_from(SourceArtifact)) or 0,
            "document_section": session.scalar(select(func.count()).select_from(DocumentSection)) or 0,
            "text_fragment": session.scalar(select(func.count()).select_from(TextFragment)) or 0,
            "knowledge_artifact": session.scalar(select(func.count()).select_from(KnowledgeArtifact)) or 0,
            "message": "snapshot counts; полноценный search/BI index — в следующих итерациях",
        }
    finally:
        session.close()

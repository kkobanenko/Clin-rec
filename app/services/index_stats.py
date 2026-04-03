"""Счётчики таблиц и обновление FTS для knowledge_artifact (TZ §19 rebuild_indexes)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select, text

from app.core.sync_database import get_sync_session, sync_engine
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.models.knowledge import KnowledgeArtifact
from app.models.text import DocumentSection, TextFragment


def refresh_knowledge_artifact_fts() -> dict[str, Any]:
    """
    Заполняет search_vector (миграция 003) для полнотекста по simple-конфигурации.
    На не-Postgres драйверах пропускаем (локальные тесты без миграции FTS).
    """
    if sync_engine.dialect.name != "postgresql":
        return {
            "fts_skipped": True,
            "reason": "dialect_not_postgresql",
            "fts_rows_updated": 0,
        }
    session = get_sync_session()
    try:
        session.execute(
            text(
                """
                UPDATE knowledge_artifact
                SET search_vector = to_tsvector(
                    'simple',
                    coalesce(title, '') || ' ' || coalesce(summary, '') || ' ' || coalesce(content_md, '')
                )
                """
            )
        )
        session.commit()
        n = session.scalar(select(func.count()).select_from(KnowledgeArtifact)) or 0
        return {"fts_skipped": False, "fts_rows_updated": int(n), "fts_config": "simple"}
    except Exception as exc:
        session.rollback()
        return {
            "fts_skipped": True,
            "fts_error": str(exc),
            "fts_rows_updated": 0,
        }
    finally:
        session.close()


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
            "message": "snapshot counts + FTS по knowledge_artifact после миграции 003 (см. rebuild_indexes)",
        }
    finally:
        session.close()

"""
Компиляция v1 compiled KB: source digest на каждый document_version и master_index.

Детерминированные slug и привязка provenance через artifact_source_link (document_version).
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.knowledge import ArtifactSourceLink, KnowledgeArtifact
from app.models.text import DocumentSection, TextFragment

logger = logging.getLogger(__name__)

COMPILER_VERSION = "0.1.0"


class KnowledgeCompileService:
    """Минимальный knowledge compiler без LLM — шаблоны digest + индекс."""

    def compile_version(self, version_id: int) -> dict[str, Any]:
        """Пересобрать source_digest для одной версии документа и обновить master_index."""
        session = get_sync_session()
        try:
            version = session.get(DocumentVersion, version_id)
            if not version:
                logger.error("DocumentVersion %s not found for compile", version_id)
                return {"status": "error", "reason": "version_not_found"}

            registry = session.get(DocumentRegistry, version.registry_id)
            if not registry:
                return {"status": "error", "reason": "registry_not_found"}

            fragment_count = (
                session.query(func.count(TextFragment.id))
                .join(DocumentSection, DocumentSection.id == TextFragment.section_id)
                .filter(DocumentSection.document_version_id == version_id)
                .scalar()
            ) or 0
            section_count = (
                session.query(func.count(DocumentSection.id))
                .filter(DocumentSection.document_version_id == version_id)
                .scalar()
            ) or 0

            canonical_slug = f"digest/v{version_id}"
            title = f"Source digest: {registry.title[:200]}"

            summary = (
                f"Документ id={registry.id}, версия id={version_id}: "
                f"{section_count} раздел(ов), {fragment_count} фрагмент(ов). "
                f"Primary source: {version.source_type_primary or 'unknown'}."
            )

            content_md = "\n".join(
                [
                    f"# {registry.title}",
                    "",
                    f"- registry_id: `{registry.id}`",
                    f"- document_version_id: `{version_id}`",
                    f"- version_hash: `{version.version_hash or ''}`",
                    f"- sections: {section_count}",
                    f"- fragments: {fragment_count}",
                    "",
                    "## Кратко",
                    summary,
                ]
            )

            artifact = session.execute(
                select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == canonical_slug)
            ).scalar_one_or_none()

            if artifact:
                artifact.title = title
                artifact.summary = summary
                artifact.content_md = content_md
                artifact.artifact_type = "source_digest"
                artifact.status = "draft"
                artifact.generator_version = COMPILER_VERSION
                artifact.manifest_json = {
                    "registry_id": registry.id,
                    "document_version_id": version_id,
                    "compiler": COMPILER_VERSION,
                }
                session.query(ArtifactSourceLink).filter(
                    ArtifactSourceLink.artifact_id == artifact.id
                ).delete(synchronize_session=False)
            else:
                artifact = KnowledgeArtifact(
                    artifact_type="source_digest",
                    title=title,
                    canonical_slug=canonical_slug,
                    status="draft",
                    content_md=content_md,
                    summary=summary,
                    confidence="medium",
                    generator_version=COMPILER_VERSION,
                    manifest_json={
                        "registry_id": registry.id,
                        "document_version_id": version_id,
                        "compiler": COMPILER_VERSION,
                    },
                )
                session.add(artifact)
                session.flush()

            session.add(
                ArtifactSourceLink(
                    artifact_id=artifact.id,
                    source_kind="document_version",
                    source_id=version_id,
                    support_type="primary",
                    notes="normalized corpus version",
                )
            )

            session.flush()
            artifact_id = artifact.id
            session.commit()
            self._rebuild_master_index(session)
            session.commit()

            logger.info("Compiled KB digest for version %s artifact_id=%s", version_id, artifact_id)
            return {
                "status": "ok",
                "artifact_id": artifact_id,
                "canonical_slug": canonical_slug,
                "fragment_count": fragment_count,
            }
        except Exception:
            session.rollback()
            logger.exception("compile_version failed for version %s", version_id)
            raise
        finally:
            session.close()

    def compile_all_current(self) -> dict[str, Any]:
        """Пересобрать digest для всех текущих версий и master_index."""
        session = get_sync_session()
        try:
            version_ids = session.execute(
                select(DocumentVersion.id).where(DocumentVersion.is_current.is_(True))
            ).scalars().all()
        finally:
            session.close()

        results = []
        for vid in version_ids:
            results.append(self.compile_version(int(vid)))
        return {"status": "ok", "versions": len(results), "results": results}

    def _rebuild_master_index(self, session) -> None:
        """Обновить единственный master_index со списком source_digest (в той же сессии)."""
        rows = session.execute(
            select(KnowledgeArtifact)
            .where(KnowledgeArtifact.artifact_type == "source_digest")
            .options(selectinload(KnowledgeArtifact.source_links))
            .order_by(KnowledgeArtifact.canonical_slug)
        ).scalars().all()

        digest_entries: list[dict[str, Any]] = []
        for art in rows:
            digest_entries.append(
                {
                    "artifact_id": art.id,
                    "slug": art.canonical_slug,
                    "title": art.title,
                    "status": art.status,
                }
            )

        manifest = {
            "compiler": COMPILER_VERSION,
            "digest_count": len(digest_entries),
            "digests": digest_entries,
        }

        idx_slug = "master_index"
        body = "\n".join(
            [
                "# Knowledge base master index",
                "",
                f"Версия компилятора: `{COMPILER_VERSION}`.",
                f"Дайджестов источников: **{len(digest_entries)}**.",
                "",
            ]
            + [f"- [{e['title']}]({e['slug']}) — id `{e['artifact_id']}`" for e in digest_entries]
        )

        master = session.execute(
            select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == idx_slug)
        ).scalar_one_or_none()

        if master:
            master.title = "Master index"
            master.content_md = body
            master.manifest_json = manifest
            master.generator_version = COMPILER_VERSION
            master.artifact_type = "master_index"
        else:
            master = KnowledgeArtifact(
                artifact_type="master_index",
                title="Master index",
                canonical_slug=idx_slug,
                status="draft",
                content_md=body,
                summary=f"Индекс из {len(digest_entries)} дайджестов",
                confidence="high",
                generator_version=COMPILER_VERSION,
                manifest_json=manifest,
            )
            session.add(master)

"""
Компиляция v1 compiled KB: source digest на каждый document_version и master_index.

Детерминированные slug и привязка provenance через artifact_source_link (document_version).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import func, select
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.knowledge import ArtifactSourceLink, EntityRegistry, KnowledgeArtifact, KnowledgeClaim
from app.models.molecule import Molecule
from app.models.text import DocumentSection, TextFragment

logger = logging.getLogger(__name__)

# Версия компилятора: поднимаем при изменении шаблонов TZ §12.3 (foundation).
COMPILER_VERSION = "0.3.0"


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
            version.compiler_version = COMPILER_VERSION

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

            content_md = self._with_frontmatter(
                "\n".join(
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
                ),
                [
                    ("artifact_type", "source_digest"),
                    ("compiler_version", COMPILER_VERSION),
                    ("registry_id", registry.id),
                    ("document_version_id", version_id),
                ],
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
            self._replace_artifact_claims(
                session,
                artifact=artifact,
                claims=[
                    {
                        "claim_type": "fact",
                        "claim_text": (
                            f"Документ registry_id={registry.id}, version_id={version_id} содержит "
                            f"{section_count} раздел(ов) и {fragment_count} фрагмент(ов); "
                            f"primary_source={version.source_type_primary or 'unknown'}."
                        ),
                        "confidence": "medium",
                        "review_status": "auto",
                        "provenance_json": {
                            "compiler": COMPILER_VERSION,
                            "registry_id": registry.id,
                            "document_version_id": version_id,
                            "artifact_slug": canonical_slug,
                        },
                    }
                ],
            )
            artifact_id = artifact.id

            # TZ §12.3 foundation-типы (без LLM): карточка документа как сущность, глоссарий, открытые вопросы.
            # Стратегия entity: для каждого document_registry создаём/находим запись entity_type=document
            # с привязкой через external_refs_json.document_registry_id (устойчиво и однозначно).
            entity = self._get_or_create_document_entity(session, registry)
            self._upsert_satellite_artifacts(session, version_id, registry, canonical_slug, entity.id)

            session.commit()
            # TZ §13: минимальные entity_page для МНН из entity_registry (lint missing_entity_page_molecule).
            self._ensure_molecule_entity_pages(session)
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

    def _get_or_create_document_entity(self, session, registry: DocumentRegistry) -> EntityRegistry:
        """
        Корпусная сущность «документ в реестре»: один EntityRegistry на document_registry_id.
        Не полагаемся на уникальность title — ключ в external_refs_json.
        """
        stmt = select(EntityRegistry).where(EntityRegistry.entity_type == "document")
        for row in session.execute(stmt).scalars().all():
            refs = row.external_refs_json or {}
            if refs.get("document_registry_id") == registry.id:
                return row
        ent = EntityRegistry(
            entity_type="document",
            canonical_name=(registry.title or f"registry-{registry.id}")[:500],
            external_refs_json={"document_registry_id": registry.id},
            aliases_json={"source": "compiler", "note": "автосоздано компилятором v1"},
            status="active",
        )
        session.add(ent)
        session.flush()
        return ent

    def _upsert_satellite_artifacts(
        self,
        session,
        version_id: int,
        registry: DocumentRegistry,
        digest_slug: str,
        entity_registry_id: int,
    ) -> None:
        """open_question, glossary_term, entity_page — с тем же provenance (document_version)."""
        digest_link_notes = "normalized corpus version"

        entity_slug = f"entity_page/registry_{registry.id}"
        entity_title = f"Entity: {registry.title[:180]}" if registry.title else f"Entity registry {registry.id}"
        entity_md = "\n".join(
            [
                f"# {entity_title}",
                "",
                f"- `entity_registry_id`: {entity_registry_id}",
                f"- `document_registry_id`: {registry.id}",
                f"- `document_version_id`: {version_id}",
                "",
                "## Связанный дайджест",
                "",
                f"См. [[{digest_slug}]].",
                "",
            ]
        )
        self._upsert_linked_artifact(
            session,
            slug=entity_slug,
            artifact_type="entity_page",
            title=entity_title,
            content_md=entity_md,
            summary=f"Корпусная сущность документа, registry_id={registry.id}",
            manifest_json={
                "compiler": COMPILER_VERSION,
                "entity_registry_id": entity_registry_id,
                "registry_id": registry.id,
                "document_version_id": version_id,
            },
            version_id=version_id,
            link_notes=digest_link_notes,
        )
        self._replace_artifact_claims(
            session,
            artifact=session.execute(
                select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == entity_slug)
            ).scalar_one(),
            claims=[
                {
                    "claim_type": "fact",
                    "claim_text": (
                        f"Document registry_id={registry.id} mapped to entity_registry_id={entity_registry_id}."
                    ),
                    "confidence": "medium",
                    "review_status": "auto",
                    "provenance_json": {
                        "compiler": COMPILER_VERSION,
                        "registry_id": registry.id,
                        "document_version_id": version_id,
                        "entity_registry_id": entity_registry_id,
                        "artifact_slug": entity_slug,
                    },
                }
            ],
        )

        glossary_slug = f"glossary/doc_{registry.id}"
        term_heading = (registry.title or f"Документ {registry.id}")[:200]
        glossary_md = "\n".join(
            [
                f"# {term_heading}",
                "",
                "Карточка термина по официальному названию клинической рекомендации в рубрикаторе.",
                "",
                f"- `document_registry_id`: `{registry.id}`",
                f"- Связанный дайджест: [[{digest_slug}]]",
                "",
            ]
        )
        self._upsert_linked_artifact(
            session,
            slug=glossary_slug,
            artifact_type="glossary_term",
            title=f"Glossary: {term_heading[:120]}",
            content_md=glossary_md,
            summary=f"Термин по названию документа id={registry.id}",
            manifest_json={
                "compiler": COMPILER_VERSION,
                "registry_id": registry.id,
                "document_version_id": version_id,
            },
            version_id=version_id,
            link_notes=digest_link_notes,
        )
        self._replace_artifact_claims(
            session,
            artifact=session.execute(
                select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == glossary_slug)
            ).scalar_one(),
            claims=[
                {
                    "claim_type": "fact",
                    "claim_text": f"Официальное название документа registry_id={registry.id}: {term_heading}.",
                    "confidence": "medium",
                    "review_status": "auto",
                    "provenance_json": {
                        "compiler": COMPILER_VERSION,
                        "registry_id": registry.id,
                        "document_version_id": version_id,
                        "artifact_slug": glossary_slug,
                    },
                }
            ],
        )

        oq_slug = f"open_questions/v{version_id}"
        oq_md = "\n".join(
            [
                "# Открытые вопросы по версии документа",
                "",
                "- Ожидается **clinical extraction**: МНН, нозологии, УУР/УДД (TZ §14).",
                "- Ожидается наполнение `entity_registry` фактическими сущностями из фрагментов.",
                "- Ожидается связка claims / provenance после извлечения (TZ §12.4).",
                "",
                f"`document_version_id`: `{version_id}`, `registry_id`: `{registry.id}`.",
                "",
                f"Дайджест источника: [[{digest_slug}]].",
                "",
            ]
        )
        self._upsert_linked_artifact(
            session,
            slug=oq_slug,
            artifact_type="open_question",
            title=f"Open questions: version {version_id}",
            content_md=oq_md,
            summary=f"Пробелы и вопросы по версии {version_id}",
            manifest_json={
                "compiler": COMPILER_VERSION,
                "registry_id": registry.id,
                "document_version_id": version_id,
            },
            version_id=version_id,
            link_notes=digest_link_notes,
        )
        self._replace_artifact_claims(
            session,
            artifact=session.execute(
                select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == oq_slug)
            ).scalar_one(),
            claims=[
                {
                    "claim_type": "hypothesis",
                    "claim_text": (
                        f"Для document_version_id={version_id} требуется дальнейшее clinical extraction "
                        "и claim/provenance enrichment."
                    ),
                    "confidence": "low",
                    "review_status": "needs_review",
                    "provenance_json": {
                        "compiler": COMPILER_VERSION,
                        "registry_id": registry.id,
                        "document_version_id": version_id,
                        "artifact_slug": oq_slug,
                    },
                }
            ],
        )

    def _upsert_linked_artifact(
        self,
        session,
        *,
        slug: str,
        artifact_type: str,
        title: str,
        content_md: str,
        summary: str,
        manifest_json: dict[str, Any],
        version_id: int,
        link_notes: str,
    ) -> KnowledgeArtifact:
        art = session.execute(
            select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == slug)
        ).scalar_one_or_none()
        if art:
            art.title = title
            art.summary = summary
            art.content_md = self._with_frontmatter(
                content_md,
                [("artifact_type", artifact_type), ("compiler_version", COMPILER_VERSION), *manifest_json.items()],
            )
            art.artifact_type = artifact_type
            art.status = "draft"
            art.generator_version = COMPILER_VERSION
            art.manifest_json = manifest_json
            session.query(ArtifactSourceLink).filter(ArtifactSourceLink.artifact_id == art.id).delete(
                synchronize_session=False
            )
        else:
            art = KnowledgeArtifact(
                artifact_type=artifact_type,
                title=title,
                canonical_slug=slug,
                status="draft",
                content_md=self._with_frontmatter(
                    content_md,
                    [("artifact_type", artifact_type), ("compiler_version", COMPILER_VERSION), *manifest_json.items()],
                ),
                summary=summary,
                confidence="medium",
                generator_version=COMPILER_VERSION,
                manifest_json=manifest_json,
            )
            session.add(art)
            session.flush()
        session.add(
            ArtifactSourceLink(
                artifact_id=art.id,
                source_kind="document_version",
                source_id=version_id,
                support_type="primary",
                notes=link_notes,
            )
        )
        session.flush()
        return art

    def _replace_artifact_claims(self, session, *, artifact: KnowledgeArtifact, claims: list[dict[str, Any]]) -> None:
        session.query(KnowledgeClaim).filter(KnowledgeClaim.artifact_id == artifact.id).delete(
            synchronize_session=False
        )
        for claim in claims:
            session.add(
                KnowledgeClaim(
                    artifact_id=artifact.id,
                    claim_type=claim["claim_type"],
                    claim_text=claim["claim_text"],
                    confidence=claim.get("confidence"),
                    review_status=claim.get("review_status"),
                    provenance_json=claim.get("provenance_json"),
                )
            )
        session.flush()

    def _with_frontmatter(self, body: str, metadata_items: list[tuple[str, Any]]) -> str:
        lines = ["---"]
        for key, value in metadata_items:
            lines.append(f"{key}: {self._yaml_scalar(value)}")
        lines.extend(["---", "", body])
        return "\n".join(lines)

    def _yaml_scalar(self, value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(value, ensure_ascii=False)

    def _ensure_molecule_entity_pages(self, session) -> None:
        """
        Для каждой строки entity_registry с entity_type=molecule и molecule_id в external_refs
        создаёт knowledge_artifact (entity_page), если страницы ещё нет. Детерминированный slug.
        """
        rows = session.execute(
            select(EntityRegistry).where(EntityRegistry.entity_type == "molecule")
        ).scalars()
        for ent in rows:
            refs = ent.external_refs_json or {}
            mid = refs.get("molecule_id")
            if mid is None:
                continue
            mid_int = int(mid)
            slug = f"entity_page/molecule_{mid_int}"
            exists = session.execute(
                select(KnowledgeArtifact.id).where(KnowledgeArtifact.canonical_slug == slug).limit(1)
            ).scalar_one_or_none()
            if exists is not None:
                continue
            mol = session.get(Molecule, mid_int)
            inn = (mol.inn_ru or "").strip() if mol else ""
            title = f"Entity: {inn[:180]}" if inn else f"Entity: molecule_id={mid_int}"
            body_lines = [
                f"# {title}",
                "",
                f"- `molecule_id`: {mid_int}",
                f"- `entity_registry_id`: {ent.id}",
                "",
            ]
            if inn:
                body_lines.insert(3, f"- `inn_ru`: {inn}")
            body = self._with_frontmatter(
                "\n".join(body_lines),
                [
                    ("artifact_type", "entity_page"),
                    ("compiler_version", COMPILER_VERSION),
                    ("molecule_id", mid_int),
                    ("entity_registry_id", ent.id),
                ],
            )
            session.add(
                KnowledgeArtifact(
                    artifact_type="entity_page",
                    title=title,
                    canonical_slug=slug,
                    status="draft",
                    content_md=body,
                    summary=f"Карточка МНН id={mid_int}",
                    confidence="medium",
                    generator_version=COMPILER_VERSION,
                    manifest_json={
                        "molecule_id": mid_int,
                        "entity_registry_id": ent.id,
                        "compiler": COMPILER_VERSION,
                    },
                )
            )
        session.flush()

    def _artifact_index_entries(self, session, artifact_type: str) -> list[dict[str, Any]]:
        rows = session.execute(
            select(KnowledgeArtifact)
            .where(KnowledgeArtifact.artifact_type == artifact_type)
            .order_by(KnowledgeArtifact.canonical_slug)
        ).scalars().all()
        return [
            {"artifact_id": a.id, "slug": a.canonical_slug, "title": a.title, "status": a.status} for a in rows
        ]

    def _rebuild_master_index(self, session) -> None:
        """Обновить master_index: дайджесты, entity pages, глоссарий, open questions (TZ §12.2)."""
        digest_entries = self._artifact_index_entries(session, "source_digest")
        entity_entries = self._artifact_index_entries(session, "entity_page")
        glossary_entries = self._artifact_index_entries(session, "glossary_term")
        openq_entries = self._artifact_index_entries(session, "open_question")

        manifest: dict[str, Any] = {
            "compiler": COMPILER_VERSION,
            "digest_count": len(digest_entries),
            "digests": digest_entries,
            "entity_page_count": len(entity_entries),
            "entity_pages": entity_entries,
            "glossary_term_count": len(glossary_entries),
            "glossary_terms": glossary_entries,
            "open_question_count": len(openq_entries),
            "open_questions": openq_entries,
        }

        def lines_for(heading: str, entries: list[dict[str, Any]]) -> list[str]:
            block: list[str] = [f"## {heading}", ""]
            for e in entries:
                block.append(f"- [{e['title']}]({e['slug']}) — id `{e['artifact_id']}`")
            block.append("")
            return block

        idx_slug = "master_index"
        nd = len(digest_entries)
        ne = len(entity_entries)
        ng = len(glossary_entries)
        nq = len(openq_entries)
        body = self._with_frontmatter(
            "\n".join(
                [
                    "# Knowledge base master index",
                    "",
                    f"Версия компилятора: `{COMPILER_VERSION}`.",
                    f"- Дайджестов источников: **{nd}**.",
                    f"- Страниц сущностей: **{ne}**.",
                    f"- Терминов глоссария: **{ng}**.",
                    f"- Реестров открытых вопросов: **{nq}**.",
                    "",
                ]
                + lines_for("Дайджесты источников (source_digest)", digest_entries)
                + lines_for("Страницы сущностей (entity_page)", entity_entries)
                + lines_for("Глоссарий (glossary_term)", glossary_entries)
                + lines_for("Открытые вопросы (open_question)", openq_entries)
            ),
            [
                ("artifact_type", "master_index"),
                ("compiler_version", COMPILER_VERSION),
                ("digest_count", nd),
                ("entity_page_count", ne),
                ("glossary_term_count", ng),
                ("open_question_count", nq),
            ],
        )
        summary_line = (
            f"Индекс: дайджесты {nd}, entity_page {ne}, glossary {ng}, open_question {nq}"
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
            master.summary = summary_line
        else:
            master = KnowledgeArtifact(
                artifact_type="master_index",
                title="Master index",
                canonical_slug=idx_slug,
                status="draft",
                content_md=body,
                summary=summary_line,
                confidence="high",
                generator_version=COMPILER_VERSION,
                manifest_json=manifest,
            )
            session.add(master)

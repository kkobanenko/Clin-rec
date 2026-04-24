"""
Минимальные health/lint правила для KB (TZ §13): orphans, digest без provenance.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Text, cast, func, select

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion
from app.models.knowledge import ArtifactSourceLink, EntityRegistry, KnowledgeArtifact, KnowledgeClaim

logger = logging.getLogger(__name__)


class KnowledgeLintService:
    ISSUE_POLICY = {
        "digest_without_provenance": {
            "severity": "warning",
            "message": "KB artifact has no provenance links.",
            "recommended_action": "Re-run KB compile and verify artifact_source_link generation.",
        },
        "duplicate_canonical_slug": {
            "severity": "blocker",
            "message": "Duplicate canonical_slug detected in KB artifacts.",
            "recommended_action": "Fix canonical slug generation and remove duplicate records.",
        },
        "artifact_empty_summary": {
            "severity": "warning",
            "message": "KB artifact summary is empty.",
            "recommended_action": "Add concise artifact summary during compile stage.",
        },
        "claims_missing_provenance_json": {
            "severity": "error",
            "message": "Non-hypothesis claims are missing provenance metadata.",
            "recommended_action": "Backfill provenance_json or regenerate claims from source-linked artifacts.",
        },
        "stale_source_version": {
            "severity": "warning",
            "message": "KB artifact references non-current document version.",
            "recommended_action": "Recompile KB artifacts using current document versions.",
        },
        "artifacts_missing_claims": {
            "severity": "warning",
            "message": "Compiler artifact has no generated claims.",
            "recommended_action": "Re-run compiler and inspect claim generation for this artifact type.",
        },
        "missing_entity_page_molecule": {
            "severity": "warning",
            "message": "Molecule entity has no entity_page artifact.",
            "recommended_action": "Run KB compile after extraction to generate molecule entity pages.",
        },
        "orphan_entity": {
            "severity": "warning",
            "message": "Entity registry entry is not linked from KB artifacts.",
            "recommended_action": "Review entity synchronization and entity_page compilation linkage.",
        },
        "conflict_group_missing_review_status": {
            "severity": "error",
            "message": "Conflict group contains claims without review status.",
            "recommended_action": "Assign review status for all claims in the conflict group.",
        },
    }

    def _issue(self, code: str, **payload: Any) -> dict[str, Any]:
        policy = self.ISSUE_POLICY.get(code, {})
        return {
            "code": code,
            "severity": policy.get("severity", "warning"),
            "message": policy.get("message", code),
            "recommended_action": policy.get("recommended_action", "Review issue details and fix source data."),
            **payload,
        }

    def run(self) -> dict[str, Any]:
        session = get_sync_session()
        try:
            issues: list[dict[str, Any]] = []

            provenance_required_types = ["source_digest", "entity_page", "glossary_term", "open_question"]

            no_link_stmt = (
                select(KnowledgeArtifact.id, KnowledgeArtifact.canonical_slug)
                .outerjoin(
                    ArtifactSourceLink,
                    ArtifactSourceLink.artifact_id == KnowledgeArtifact.id,
                )
                .where(
                    KnowledgeArtifact.artifact_type.in_(provenance_required_types),
                    ArtifactSourceLink.id.is_(None),
                )
            )
            for aid, slug in session.execute(no_link_stmt).all():
                issues.append(self._issue("digest_without_provenance", artifact_id=aid, slug=slug))

            duplicate_slug_stmt = (
                select(KnowledgeArtifact.canonical_slug, func.count(KnowledgeArtifact.id))
                .group_by(KnowledgeArtifact.canonical_slug)
                .having(func.count(KnowledgeArtifact.id) > 1)
            )
            for slug, count in session.execute(duplicate_slug_stmt).all():
                issues.append(self._issue("duplicate_canonical_slug", slug=slug, count=int(count)))

            empty_summary_stmt = select(KnowledgeArtifact.id, KnowledgeArtifact.canonical_slug).where(
                KnowledgeArtifact.summary.is_(None)
                | (func.trim(KnowledgeArtifact.summary) == "")
            )
            for aid, slug in session.execute(empty_summary_stmt).all():
                issues.append(self._issue("artifact_empty_summary", artifact_id=aid, slug=slug))

            claims_no_prov = session.scalar(
                select(func.count())
                .select_from(KnowledgeClaim)
                .where(
                    (KnowledgeClaim.provenance_json.is_(None) | (cast(KnowledgeClaim.provenance_json, Text) == "null")),
                    KnowledgeClaim.claim_type != "hypothesis",
                )
            ) or 0
            if claims_no_prov:
                issues.append(self._issue("claims_missing_provenance_json", count=claims_no_prov))

            stale_source_stmt = (
                select(
                    KnowledgeArtifact.id,
                    KnowledgeArtifact.canonical_slug,
                    ArtifactSourceLink.source_id,
                )
                .join(ArtifactSourceLink, ArtifactSourceLink.artifact_id == KnowledgeArtifact.id)
                .join(DocumentVersion, DocumentVersion.id == ArtifactSourceLink.source_id)
                .where(
                    ArtifactSourceLink.source_kind == "document_version",
                    KnowledgeArtifact.artifact_type.in_(provenance_required_types),
                    DocumentVersion.is_current.is_(False),
                )
            )
            for aid, slug, source_id in session.execute(stale_source_stmt).all():
                issues.append(
                    self._issue(
                        "stale_source_version",
                        artifact_id=aid,
                        slug=slug,
                        document_version_id=int(source_id),
                    )
                )

            missing_claim_stmt = (
                select(KnowledgeArtifact.id, KnowledgeArtifact.canonical_slug)
                .join(ArtifactSourceLink, ArtifactSourceLink.artifact_id == KnowledgeArtifact.id)
                .outerjoin(KnowledgeClaim, KnowledgeClaim.artifact_id == KnowledgeArtifact.id)
                .where(
                    KnowledgeArtifact.artifact_type.in_(
                        ["source_digest", "entity_page", "glossary_term", "open_question"]
                    ),
                    ArtifactSourceLink.source_kind == "document_version",
                    KnowledgeClaim.id.is_(None),
                )
            )
            for aid, slug in session.execute(missing_claim_stmt).all():
                issues.append(self._issue("artifacts_missing_claims", artifact_id=aid, slug=slug))

            # TZ §13: entity_page для молекул в entity_registry (после extract).
            covered_molecules: set[int] = set()
            for art in session.execute(
                select(KnowledgeArtifact).where(KnowledgeArtifact.artifact_type == "entity_page")
            ).scalars():
                mj = (art.manifest_json or {}).get("molecule_id")
                if mj is not None:
                    covered_molecules.add(int(mj))
            for ent in session.execute(
                select(EntityRegistry).where(EntityRegistry.entity_type == "molecule")
            ).scalars():
                refs = ent.external_refs_json or {}
                mid = refs.get("molecule_id")
                if mid is None:
                    continue
                mid_int = int(mid)
                if mid_int not in covered_molecules:
                    issues.append(
                        self._issue("missing_entity_page_molecule", entity_registry_id=ent.id, molecule_id=mid_int)
                    )

            linked_entity_ids: set[int] = set()
            for art in session.execute(
                select(KnowledgeArtifact).where(KnowledgeArtifact.artifact_type == "entity_page")
            ).scalars():
                manifest = art.manifest_json or {}
                entity_id = manifest.get("entity_registry_id")
                if entity_id is None:
                    continue
                linked_entity_ids.add(int(entity_id))

            for ent in session.execute(
                select(EntityRegistry).where(EntityRegistry.entity_type.in_(["document", "molecule"]))
            ).scalars():
                if ent.id in linked_entity_ids:
                    continue
                issues.append(self._issue("orphan_entity", entity_registry_id=ent.id, entity_type=ent.entity_type))

            conflict_missing_review_stmt = (
                select(KnowledgeClaim.conflict_group_id, func.count(KnowledgeClaim.id))
                .where(
                    KnowledgeClaim.conflict_group_id.isnot(None),
                    KnowledgeClaim.review_status.is_(None),
                )
                .group_by(KnowledgeClaim.conflict_group_id)
            )
            for group_id, count in session.execute(conflict_missing_review_stmt).all():
                issues.append(
                    self._issue(
                        "conflict_group_missing_review_status",
                        conflict_group_id=int(group_id),
                        claim_count=int(count),
                    )
                )

            # Незакрытые группы конфликтов: distinct conflict_group_id среди claims.
            conflict_groups = (
                session.scalar(
                    select(func.count(func.distinct(KnowledgeClaim.conflict_group_id))).where(
                        KnowledgeClaim.conflict_group_id.isnot(None)
                    )
                )
                or 0
            )

            result = {
                "status": "ok",
                "issue_count": len(issues),
                "issues": issues,
                "conflict_groups_distinct": int(conflict_groups),
            }
            logger.info("lint_kb: %s issues, conflict_groups=%s", len(issues), conflict_groups)
            return result
        finally:
            session.close()

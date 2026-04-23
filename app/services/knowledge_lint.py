"""
Минимальные health/lint правила для KB (TZ §13): orphans, digest без provenance.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select

from app.core.sync_database import get_sync_session
from app.models.knowledge import ArtifactSourceLink, EntityRegistry, KnowledgeArtifact, KnowledgeClaim

logger = logging.getLogger(__name__)


class KnowledgeLintService:
    def run(self) -> dict[str, Any]:
        session = get_sync_session()
        try:
            issues: list[dict[str, Any]] = []

            no_link_stmt = (
                select(KnowledgeArtifact.id, KnowledgeArtifact.canonical_slug)
                .outerjoin(
                    ArtifactSourceLink,
                    ArtifactSourceLink.artifact_id == KnowledgeArtifact.id,
                )
                .where(
                    KnowledgeArtifact.artifact_type == "source_digest",
                    ArtifactSourceLink.id.is_(None),
                )
            )
            for aid, slug in session.execute(no_link_stmt).all():
                issues.append(
                    {
                        "code": "digest_without_provenance",
                        "artifact_id": aid,
                        "slug": slug,
                    }
                )

            claims_no_prov = session.scalar(
                select(func.count())
                .select_from(KnowledgeClaim)
                .where(
                    KnowledgeClaim.provenance_json.is_(None),
                    KnowledgeClaim.claim_type != "hypothesis",
                )
            ) or 0
            if claims_no_prov:
                issues.append(
                    {
                        "code": "claims_missing_provenance_json",
                        "count": claims_no_prov,
                    }
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
                issues.append(
                    {
                        "code": "artifacts_missing_claims",
                        "artifact_id": aid,
                        "slug": slug,
                    }
                )

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
                        {
                            "code": "missing_entity_page_molecule",
                            "entity_registry_id": ent.id,
                            "molecule_id": mid_int,
                        }
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

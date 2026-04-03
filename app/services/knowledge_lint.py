"""
Минимальные health/lint правила для KB (TZ §13): orphans, digest без provenance.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select

from app.core.sync_database import get_sync_session
from app.models.knowledge import ArtifactSourceLink, KnowledgeArtifact, KnowledgeClaim

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

            result = {
                "status": "ok",
                "issue_count": len(issues),
                "issues": issues,
            }
            logger.info("lint_kb: %s issues", len(issues))
            return result
        finally:
            session.close()

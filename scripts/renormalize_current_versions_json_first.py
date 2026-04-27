#!/usr/bin/env python3
"""Re-normalize current document versions using JSON-first policy.

This script is offline-safe: it only works with already persisted local artifacts.
"""

from __future__ import annotations

import json
from collections import Counter

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion, SourceArtifact
from app.models.text import DocumentSection, TextFragment
from app.services.normalize import NormalizeService


def run() -> int:
    session = get_sync_session()
    normalize_service = NormalizeService()
    try:
        current_versions = (
            session.query(DocumentVersion)
            .filter(DocumentVersion.is_current.is_(True))
            .order_by(DocumentVersion.id.asc())
            .all()
        )

        summary: dict[str, object] = {
            "total_current_versions": len(current_versions),
            "versions_with_json_artifact": 0,
            "normalized": {"success": 0, "degraded": 0, "failed": 0},
            "sections_from_json": 0,
            "fragments_from_json": 0,
            "fallback_to_html_pdf_count": 0,
            "per_version": [],
        }

        status_counter: Counter[str] = Counter()
        fallback_count = 0

        for version in current_versions:
            json_artifact = (
                session.query(SourceArtifact)
                .filter(
                    SourceArtifact.document_version_id == version.id,
                    SourceArtifact.artifact_type == "json",
                )
                .first()
            )
            if json_artifact is None:
                summary["per_version"].append(  # type: ignore[index]
                    {
                        "version_id": version.id,
                        "registry_id": version.registry_id,
                        "status": "skipped",
                        "reason_code": "json_artifact_missing",
                    }
                )
                continue

            summary["versions_with_json_artifact"] = int(summary["versions_with_json_artifact"]) + 1
            result = normalize_service.normalize(version.id)
            status_counter[result.status] += 1
            if result.source_used in {"html_fallback", "pdf_fallback"}:
                fallback_count += 1

            summary["per_version"].append(  # type: ignore[index]
                {
                    "version_id": version.id,
                    "registry_id": version.registry_id,
                    "status": result.status,
                    "source_used": result.source_used,
                    "reason_code": result.reason_code,
                    "sections_count": result.sections_count,
                    "fragments_count": result.fragments_count,
                }
            )

        normalized = summary["normalized"]  # type: ignore[assignment]
        assert isinstance(normalized, dict)
        normalized["success"] = int(status_counter.get("success", 0))
        normalized["degraded"] = int(status_counter.get("degraded", 0))
        normalized["failed"] = int(status_counter.get("failed", 0))
        summary["fallback_to_html_pdf_count"] = fallback_count

        sections_from_json = (
            session.query(DocumentSection)
            .join(DocumentVersion, DocumentVersion.id == DocumentSection.document_version_id)
            .filter(
                DocumentVersion.is_current.is_(True),
                DocumentSection.source_artifact_type == "json",
            )
            .count()
        )
        fragments_from_json = (
            session.query(TextFragment)
            .join(DocumentSection, DocumentSection.id == TextFragment.section_id)
            .join(DocumentVersion, DocumentVersion.id == DocumentSection.document_version_id)
            .filter(
                DocumentVersion.is_current.is_(True),
                TextFragment.source_artifact_type == "json",
            )
            .count()
        )

        summary["sections_from_json"] = sections_from_json
        summary["fragments_from_json"] = fragments_from_json

        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(run())

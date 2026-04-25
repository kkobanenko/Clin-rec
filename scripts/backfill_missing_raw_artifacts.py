#!/usr/bin/env python3
"""Backfill missing raw artifacts for current document versions.

Usage:
    python scripts/backfill_missing_raw_artifacts.py [--dry-run]

Finds all current document versions without valid downloadable artifacts
and attempts to re-run the fetch stage for each. Does not delete existing
artifacts. Produces a JSON report.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.core.storage import download_artifact
from app.services.artifact_validation import validate_artifact_payload


def _get_valid_artifact_count(session, version_id: int) -> int:
    artifacts = (
        session.query(SourceArtifact)
        .filter_by(document_version_id=version_id)
        .all()
    )
    valid = 0
    for artifact in artifacts:
        try:
            raw = download_artifact(artifact.raw_path)
        except Exception:
            continue
        if not raw:
            continue
        v = validate_artifact_payload(artifact.artifact_type, artifact.content_type, raw)
        if v.is_valid:
            valid += 1
    return valid


def main():
    parser = argparse.ArgumentParser(description="Backfill missing raw artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually queue fetches")
    args = parser.parse_args()

    session = get_sync_session()

    docs = session.query(DocumentRegistry).order_by(DocumentRegistry.id).all()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "summary": {
            "total_documents": 0,
            "without_current_version": 0,
            "already_have_artifacts": 0,
            "queued_fetch": 0,
            "fetch_failed": 0,
        },
        "details": [],
    }

    for doc in docs:
        report["summary"]["total_documents"] += 1

        version = (
            session.query(DocumentVersion)
            .filter_by(registry_id=doc.id, is_current=True)
            .order_by(DocumentVersion.detected_at.desc())
            .first()
        )

        if version is None:
            report["summary"]["without_current_version"] += 1
            report["details"].append({
                "document_id": doc.id,
                "title": doc.title,
                "status": "no_current_version",
            })
            continue

        valid_count = _get_valid_artifact_count(session, version.id)

        if valid_count > 0:
            report["summary"]["already_have_artifacts"] += 1
            report["details"].append({
                "document_id": doc.id,
                "title": doc.title,
                "version_id": version.id,
                "status": "ok",
                "valid_artifacts": valid_count,
            })
            continue

        entry = {
            "document_id": doc.id,
            "title": doc.title,
            "version_id": version.id,
            "html_url": doc.html_url,
            "pdf_url": doc.pdf_url,
            "valid_artifacts": 0,
        }

        if args.dry_run:
            entry["status"] = "would_fetch"
            report["summary"]["queued_fetch"] += 1
        else:
            try:
                from app.workers.tasks.fetch import fetch_document
                fetch_document.delay(version.id)
                entry["status"] = "queued"
                report["summary"]["queued_fetch"] += 1
            except Exception as exc:
                entry["status"] = "error"
                entry["error"] = str(exc)
                report["summary"]["fetch_failed"] += 1

        report["details"].append(entry)

    session.close()

    # Write report
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_dir = Path(__file__).parent.parent / ".artifacts" / "manual_checks" / ts
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "raw_artifact_backfill_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report["summary"], indent=2))
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()

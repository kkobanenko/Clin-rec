"""Синхронные операции с output_release для Celery (создание черновика, output filing)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.sync_database import get_sync_session
from app.models.knowledge import KnowledgeArtifact, OutputRelease

logger = logging.getLogger(__name__)

GENERATOR_VERSION = "0.2.0"


def _ensure_output_artifact(session, row: OutputRelease) -> KnowledgeArtifact | None:
    if row.artifact_id or not row.file_pointer:
        return None

    artifact = KnowledgeArtifact(
        artifact_type="output_release",
        title=row.title,
        canonical_slug=f"output/{row.output_type}/{row.id}",
        status="published",
        content_md=None,
        summary=f"Filed output release #{row.id}",
        review_status=row.review_status,
        generator_version=row.generator_version,
        storage_path=row.file_pointer,
        manifest_json={
            "output_release_id": row.id,
            "output_type": row.output_type,
            "file_pointer": row.file_pointer,
        },
    )
    session.add(artifact)
    session.flush()
    row.artifact_id = artifact.id
    return artifact


def _build_memo_markdown(
    session,
    output_id: int,
    scope_json: dict | None,
) -> tuple[str, dict]:
    """
    Простой Markdown-memo: список последних дайджестов или slug из scope_json.
    Возвращает (текст файла, memo_manifest для scope_json).
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    lines: list[str] = [
        "---",
        "output_type: memo",
        f"output_release_id: {output_id}",
        f"generator_version: {GENERATOR_VERSION}",
        f"generated_at: {generated_at}",
        "review_status: pending_review",
        "source_artifacts:",
    ]
    manifest: dict = {"generator_version": GENERATOR_VERSION, "digest_slugs": []}
    scope = scope_json or {}
    limit = int(scope.get("digest_limit", 10))
    if scope.get("digest_slugs"):
        for slug in scope["digest_slugs"]:
            manifest["digest_slugs"].append(slug)
            lines.append(f"  - {slug}")
    else:
        rows = session.execute(
            select(KnowledgeArtifact.canonical_slug, KnowledgeArtifact.title)
            .where(KnowledgeArtifact.artifact_type == "source_digest")
            .order_by(KnowledgeArtifact.id.desc())
            .limit(limit)
        ).all()
        for slug, title in rows:
            manifest["digest_slugs"].append(str(slug))
            lines.append(f"  - {slug}")
    lines.extend(
        [
            "---",
            "",
            "> Internal analytical draft. Not a medical recommendation.",
            "> Requires human review before release.",
            "",
            "# Analytic memo",
            "",
            "## Source digest links",
            "",
        ]
    )
    for slug in manifest["digest_slugs"]:
        lines.append(f"- [[{slug}]]")
    body = "\n".join(lines) + "\n"
    return body, manifest


def _write_output_file(output_id: int, output_type: str, body: str) -> Path:
    """Сохраняем UTF-8 файл под управляемым префиксом каталога (см. CRIN_OUTPUT_FILES_DIR)."""
    root = Path(settings.output_files_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{output_type}_{output_id}.md"
    path.write_text(body, encoding="utf-8")
    return path.resolve()


def create_pending_output(
    output_type: str,
    title: str | None = None,
    scope_json: dict | None = None,
    generator_version: str = GENERATOR_VERSION,
) -> int:
    """
    Создать output_release; для memo — сразу пишем markdown на диск и ставим file_pointer (TZ §16).
    """
    session = get_sync_session()
    try:
        safe_title = (title or "").strip() or f"{output_type} draft"
        row = OutputRelease(
            output_type=output_type,
            title=safe_title,
            scope_json=scope_json,
            generator_version=generator_version,
            review_status="pending_review",
            file_back_status="pending",
        )
        session.add(row)
        session.flush()
        oid = row.id

        if output_type == "memo":
            body, memo_manifest = _build_memo_markdown(session, oid, scope_json)
            path = _write_output_file(oid, "memo", body)
            row.file_pointer = str(path)
            merged_scope = dict(scope_json or {})
            merged_scope["memo_manifest"] = memo_manifest
            row.scope_json = merged_scope

        session.commit()
        session.refresh(row)
        logger.info("Created output_release id=%s type=%s pointer=%s", row.id, output_type, row.file_pointer)
        return row.id
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def apply_file_back(output_id: int, file_back_status: str) -> dict:
    """Обновить статус filing; при accepted проставить released_at и review_status."""
    session = get_sync_session()
    try:
        row = session.get(OutputRelease, output_id)
        if not row:
            logger.warning("output_release %s not found", output_id)
            return {"status": "error", "reason": "output_not_found", "output_id": output_id}

        row.file_back_status = file_back_status
        if file_back_status == "accepted":
            row.released_at = datetime.now(timezone.utc)
            row.review_status = "approved"
            artifact = _ensure_output_artifact(session, row)
        elif file_back_status == "rejected":
            row.review_status = "rejected"
            artifact = None
        else:
            row.review_status = "pending_review"
            artifact = None

        session.commit()
        logger.info("file_back output_id=%s status=%s", output_id, file_back_status)
        return {
            "status": "ok",
            "output_id": output_id,
            "file_back_status": file_back_status,
            "artifact_id": row.artifact_id,
            "artifact_created": artifact is not None,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

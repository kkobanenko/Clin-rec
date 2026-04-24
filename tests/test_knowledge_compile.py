from uuid import uuid4

from sqlalchemy import select

from app.models.document import DocumentRegistry, DocumentVersion
from app.models.knowledge import KnowledgeArtifact
from app.services.knowledge_compile import KnowledgeCompileService


def _seed_document(sync_session) -> int:
    reg = DocumentRegistry(
        external_id=f"compile-{uuid4().hex}",
        title="KB compile frontmatter test",
        card_url="http://example.local/card",
    )
    sync_session.add(reg)
    sync_session.flush()
    version = DocumentVersion(
        registry_id=reg.id,
        version_hash=f"vh-{uuid4().hex[:12]}",
        source_type_primary="html",
        is_current=True,
    )
    sync_session.add(version)
    sync_session.flush()
    return int(version.id)


def test_compile_writes_richer_frontmatter(sync_session, monkeypatch):
    version_id = _seed_document(sync_session)
    monkeypatch.setattr(sync_session, "close", lambda: None)
    monkeypatch.setattr("app.services.knowledge_compile.get_sync_session", lambda: sync_session)

    out = KnowledgeCompileService().compile_version(version_id)

    assert out["status"] == "ok"
    digest = sync_session.execute(
        select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == f"digest/v{version_id}")
    ).scalar_one()
    body = digest.content_md or ""
    assert "artifact_type: \"source_digest\"" in body
    assert "generator_version: \"0.3.0\"" in body
    assert "source_document_version_ids:" in body
    assert "source_hashes:" in body
    assert "review_status: \"auto\"" in body
    assert "claim_count: 1" in body
    assert "generated_at:" in body


def test_master_index_includes_warning_counts(sync_session, monkeypatch):
    # Seed an orphan artifact to ensure warning counters are populated.
    sync_session.add(
        KnowledgeArtifact(
            artifact_type="source_digest",
            title="Orphan warning artifact",
            canonical_slug=f"warnings/{uuid4().hex}",
            status="draft",
            summary="",
        )
    )
    sync_session.flush()

    version_id = _seed_document(sync_session)
    monkeypatch.setattr(sync_session, "close", lambda: None)
    monkeypatch.setattr("app.services.knowledge_compile.get_sync_session", lambda: sync_session)

    out = KnowledgeCompileService().compile_version(version_id)
    assert out["status"] == "ok"

    master = sync_session.execute(
        select(KnowledgeArtifact).where(KnowledgeArtifact.canonical_slug == "master_index")
    ).scalar_one()
    manifest = master.manifest_json or {}
    warning_counts = manifest.get("warning_counts")
    assert isinstance(warning_counts, dict)
    assert "empty_summary" in warning_counts
    assert "missing_provenance" in warning_counts
    assert warning_counts["empty_summary"] >= 1
    assert warning_counts["missing_provenance"] >= 1

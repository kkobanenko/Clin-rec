from uuid import uuid4

from app.models.knowledge import KnowledgeArtifact, KnowledgeClaim
from app.services.knowledge_lint import KnowledgeLintService


def test_lint_catches_missing_provenance_for_non_hypothesis(sync_session, monkeypatch):
    artifact = KnowledgeArtifact(
        artifact_type="source_digest",
        title="Lint provenance test",
        canonical_slug=f"lint/provenance/{uuid4().hex}",
        status="draft",
        summary="summary",
    )
    sync_session.add(artifact)
    sync_session.flush()
    sync_session.add(
        KnowledgeClaim(
            artifact_id=artifact.id,
            claim_type="fact",
            claim_text="claim without provenance",
            review_status="auto",
            provenance_json=None,
        )
    )
    sync_session.flush()

    monkeypatch.setattr(sync_session, "close", lambda: None)
    monkeypatch.setattr("app.services.knowledge_lint.get_sync_session", lambda: sync_session)

    out = KnowledgeLintService().run()

    issue = next((item for item in out["issues"] if item.get("code") == "claims_missing_provenance_json"), None)
    assert issue is not None
    assert issue["count"] >= 1


def test_lint_catches_empty_summary(sync_session, monkeypatch):
    artifact = KnowledgeArtifact(
        artifact_type="entity_page",
        title="Lint summary test",
        canonical_slug=f"lint/summary/{uuid4().hex}",
        status="draft",
        summary="",
    )
    sync_session.add(artifact)
    sync_session.flush()

    monkeypatch.setattr(sync_session, "close", lambda: None)
    monkeypatch.setattr("app.services.knowledge_lint.get_sync_session", lambda: sync_session)

    out = KnowledgeLintService().run()

    assert any(
        item.get("code") == "artifact_empty_summary" and item.get("artifact_id") == artifact.id
        for item in out["issues"]
    )

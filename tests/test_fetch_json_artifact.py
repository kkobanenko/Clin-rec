from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.services.fetch import FetchService


def _clear(session):
    session.query(SourceArtifact).delete()
    session.query(DocumentVersion).delete()
    session.query(DocumentRegistry).delete()
    session.commit()


def test_fetch_persists_source_payload_as_json_artifact(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)
    uploaded: dict[str, bytes] = {}
    queued: list[int] = []

    monkeypatch.setattr("app.services.fetch.get_sync_session", lambda: session_factory())
    monkeypatch.setattr(
        "app.services.fetch.upload_artifact",
        lambda data, key, _content_type: uploaded.setdefault(key, data),
    )
    monkeypatch.setattr(
        "app.workers.tasks.normalize.normalize_document.delay",
        lambda version_id: queued.append(version_id),
    )

    setup = session_factory()
    _clear(setup)
    registry = DocumentRegistry(
        external_id="json-only-doc",
        title="JSON only",
        source_payload_json={"title": "A", "rules": ["1", "X"]},
        discovered_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    setup.add(registry)
    setup.flush()
    version = DocumentVersion(
        registry_id=registry.id,
        source_type_primary="json",
        source_type_available="json",
        is_current=True,
    )
    setup.add(version)
    setup.commit()
    version_id = version.id
    doc_id = registry.id
    setup.close()

    result = FetchService().fetch(version_id)
    assert result.status == "success"
    assert result.fetched_artifacts == ("json",)
    assert result.queued_normalize is True
    assert queued == [version_id]

    verify = session_factory()
    artifacts = verify.query(SourceArtifact).filter_by(document_version_id=version_id).all()
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.artifact_type == "json"
    assert artifact.raw_path == f"documents/{doc_id}/versions/{version_id}/raw_json.json"
    assert artifact.content_hash
    assert artifact.raw_path in uploaded

    second_result = FetchService().fetch(version_id)
    assert second_result.status == "success"
    artifacts_again = verify.query(SourceArtifact).filter_by(document_version_id=version_id).all()
    assert len(artifacts_again) == 1

    _clear(verify)
    verify.close()
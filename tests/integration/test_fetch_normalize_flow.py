from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.models.text import DocumentSection, TextFragment
from app.services.fetch import FetchService
from app.services.normalize import NormalizeService


class DummyResponse:
    def __init__(self, content: bytes, content_type: str = "text/html"):
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None


class DummyClient:
    def __init__(self, response: DummyResponse):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url):
        return self._response


def _clear_document_tables(session):
    session.query(TextFragment).delete()
    session.query(DocumentSection).delete()
    session.query(SourceArtifact).delete()
    session.query(DocumentVersion).delete()
    session.query(DocumentRegistry).delete()
    session.commit()


def test_fetch_then_normalize_html_flow(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)
    artifact_store: dict[str, bytes] = {}
    queued_normalize: list[int] = []
    queued_extract: list[int] = []

    html = b"""
    <html>
      <body>
        <main>
          <h1>1. Definition</h1>
          <p>Clinical recommendation introduction text.</p>
          <h2>2. Therapy</h2>
          <p>Insulin therapy details.</p>
          <ul><li>Monitor glucose</li></ul>
        </main>
      </body>
    </html>
    """

    monkeypatch.setattr("app.services.fetch.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.normalize.get_sync_session", lambda: session_factory())
    monkeypatch.setattr(
        "app.services.fetch.httpx.Client",
        lambda **kwargs: DummyClient(DummyResponse(html, "text/html")),
    )
    monkeypatch.setattr(
        "app.services.fetch.upload_artifact",
        lambda data, key, content_type: artifact_store.setdefault(key, data) or key,
    )
    monkeypatch.setattr(
        "app.services.normalize.download_artifact",
        lambda key: artifact_store[key],
    )
    monkeypatch.setattr(
        "app.workers.tasks.normalize.normalize_document.delay",
        lambda version_id: queued_normalize.append(version_id),
    )
    monkeypatch.setattr(
        "app.workers.tasks.extract.extract_document.delay",
        lambda version_id: queued_extract.append(version_id),
    )

    setup_session = session_factory()
    _clear_document_tables(setup_session)
    registry = DocumentRegistry(
        external_id="test-doc-1",
        title="Test Clinical Document",
        html_url="https://example.test/document",
        pdf_url=None,
        discovered_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    setup_session.add(registry)
    setup_session.flush()
    version = DocumentVersion(
        registry_id=registry.id,
        source_type_primary="html",
        source_type_available="html",
        is_current=True,
    )
    setup_session.add(version)
    setup_session.commit()
    version_id = version.id
    registry_id = registry.id
    setup_session.close()

    fetch_result = FetchService().fetch(version_id)
    assert fetch_result.status == "success"
    assert fetch_result.fetched_artifacts == ("html",)
    assert fetch_result.queued_normalize is True
    assert queued_normalize == [version_id]
    assert artifact_store

    normalize_result = NormalizeService().normalize(version_id)
    assert normalize_result.status == "success"
    assert normalize_result.sections_count == 2
    assert normalize_result.fragments_count == 3
    assert normalize_result.source_used in {"html", "html_fallback"}
    assert normalize_result.queued_extract is True
    assert queued_extract == [version_id]

    verify_session = session_factory()
    stored_version = verify_session.get(DocumentVersion, version_id)
    artifacts = verify_session.query(SourceArtifact).filter_by(document_version_id=version_id).all()
    sections = (
        verify_session.query(DocumentSection)
        .filter_by(document_version_id=version_id)
        .order_by(DocumentSection.section_order)
        .all()
    )
    fragments = (
        verify_session.query(TextFragment)
        .join(DocumentSection, DocumentSection.id == TextFragment.section_id)
        .filter(DocumentSection.document_version_id == version_id)
        .order_by(TextFragment.fragment_order)
        .all()
    )

    assert stored_version is not None
    assert stored_version.registry_id == registry_id
    assert stored_version.version_hash is not None
    assert stored_version.normalizer_version == "1.0.0"
    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == "html"
    assert len(sections) == 2
    assert sections[0].section_title == "1. Definition"
    assert sections[1].section_title == "2. Therapy"
    assert len(fragments) == 3
    assert [fragment.fragment_type for fragment in fragments] == ["paragraph", "paragraph", "bullet"]

    _clear_document_tables(verify_session)
    verify_session.close()


def test_normalize_json_creates_derived_blocks_artifact(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)
    artifact_store: dict[str, bytes] = {}
    queued_extract: list[int] = []

    monkeypatch.setattr("app.services.normalize.get_sync_session", lambda: session_factory())
    monkeypatch.setattr(
        "app.services.normalize.download_artifact",
        lambda key: artifact_store[key],
    )
    monkeypatch.setattr(
        "app.services.normalize.upload_artifact",
        lambda data, key, content_type: artifact_store.setdefault(key, data) or key,
    )
    monkeypatch.setattr(
        "app.workers.tasks.extract.extract_document.delay",
        lambda version_id: queued_extract.append(version_id),
    )

    setup_session = session_factory()
    _clear_document_tables(setup_session)
    registry = DocumentRegistry(
        external_id="json-derived-blocks-doc",
        title="JSON Doc",
        discovered_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    setup_session.add(registry)
    setup_session.flush()
    version = DocumentVersion(
        registry_id=registry.id,
        source_type_primary="json",
        source_type_available="json",
        is_current=True,
    )
    setup_session.add(version)
    setup_session.flush()
    json_artifact = SourceArtifact(
        document_version_id=version.id,
        artifact_type="json",
        raw_path=f"documents/{registry.id}/versions/{version.id}/raw_json.json",
        content_hash="h-json",
        content_type="application/json",
        headers_json={},
        fetched_at=datetime.now(timezone.utc),
    )
    setup_session.add(json_artifact)
    setup_session.commit()

    artifact_store[json_artifact.raw_path] = (
        b'{"title":"Section A","rules":["1","alpha"],"html":"<p>Beta</p>","image_ref":"img-1"}'
    )

    result = NormalizeService().normalize(version.id)
    assert result.status == "success"
    assert result.source_used == "json"
    assert queued_extract == [version.id]

    verify_session = session_factory()
    artifacts = verify_session.query(SourceArtifact).filter_by(document_version_id=version.id).all()
    derived = [a for a in artifacts if a.artifact_type == "derived_blocks"]
    assert derived
    derived_payload = artifact_store[derived[0].raw_path].decode("utf-8")
    assert '"schema_version": "canonical_json_blocks_v1"' in derived_payload
    assert '"source_artifact_type": "json"' in derived_payload
    assert '"content_kind": "image"' in derived_payload

    _clear_document_tables(verify_session)
    verify_session.close()
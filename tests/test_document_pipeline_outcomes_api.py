from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.dependencies import get_db
from app.main import app


class FakeScalarResult:
    def __init__(self, value=None, values=None):
        self._value = value
        self._values = values or []

    def scalar_one(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return self._values


class FakeTupleResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeAsyncSession:
    def __init__(self, responses):
        self._responses = list(responses)

    async def execute(self, _query):
        if not self._responses:
            raise AssertionError("Unexpected execute call")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_document_endpoints_expose_pipeline_outcome():
    event = SimpleNamespace(
        stage="normalize",
        status="degraded",
        message="Normalize stage finished with status=degraded",
        detail_json={"reason_code": "normalize_empty_after_pdf_fallback"},
        created_at=datetime.now(timezone.utc),
    )
    section = SimpleNamespace(id=7, section_path="1", section_title="Intro", section_order=0)
    fragment = SimpleNamespace(
        id=13,
        section_id=7,
        fragment_order=0,
        fragment_type="paragraph",
        fragment_text="Normalized fragment text",
        stable_id="frag-1",
    )

    content_db = FakeAsyncSession(
        [
            FakeScalarResult(value=SimpleNamespace(id=11)),
            FakeScalarResult(values=[section]),
            FakeScalarResult(value=event),
        ]
    )
    fragments_db = FakeAsyncSession(
        [
            FakeScalarResult(value=SimpleNamespace(id=11)),
            FakeTupleResult(rows=[(7,)]),
            FakeScalarResult(values=[fragment]),
            FakeScalarResult(value=event),
        ]
    )
    sessions = [content_db, fragments_db]

    async def override_get_db():
        if not sessions:
            raise AssertionError("No fake session left")
        yield sessions.pop(0)

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            content_resp = await client.get("/documents/1/content")
            assert content_resp.status_code == 200
            content_data = content_resp.json()
            assert content_data["pipeline_outcome"]["stage"] == "normalize"
            assert content_data["pipeline_outcome"]["status"] == "degraded"
            assert content_data["pipeline_outcome"]["reason_code"] == "normalize_empty_after_pdf_fallback"
            assert len(content_data["sections"]) == 1

            fragments_resp = await client.get("/documents/1/fragments")
            assert fragments_resp.status_code == 200
            fragments_data = fragments_resp.json()
            assert fragments_data["pipeline_outcome"]["stage"] == "normalize"
            assert fragments_data["pipeline_outcome"]["reason_code"] == "normalize_empty_after_pdf_fallback"
            assert fragments_data["total"] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_document_endpoints_prefer_success_outcome_when_content_exists():
    success_event = SimpleNamespace(
        stage="fetch",
        status="success",
        message="Fetch stage finished with status=success",
        detail_json={"queued_normalize": True},
        created_at=datetime.now(timezone.utc),
    )
    section = SimpleNamespace(id=7, section_path="1", section_title="Intro", section_order=0)
    fragment = SimpleNamespace(
        id=13,
        section_id=7,
        fragment_order=0,
        fragment_type="paragraph",
        fragment_text="Normalized fragment text",
        stable_id="frag-1",
    )

    content_db = FakeAsyncSession(
        [
            FakeScalarResult(value=SimpleNamespace(id=11)),
            FakeScalarResult(values=[section]),
            FakeScalarResult(value=success_event),
        ]
    )
    fragments_db = FakeAsyncSession(
        [
            FakeScalarResult(value=SimpleNamespace(id=11)),
            FakeTupleResult(rows=[(7,)]),
            FakeScalarResult(values=[fragment]),
            FakeScalarResult(value=success_event),
        ]
    )
    sessions = [content_db, fragments_db]

    async def override_get_db():
        if not sessions:
            raise AssertionError("No fake session left")
        yield sessions.pop(0)

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            content_resp = await client.get("/documents/1/content")
            assert content_resp.status_code == 200
            content_data = content_resp.json()
            assert content_data["pipeline_outcome"]["stage"] == "fetch"
            assert content_data["pipeline_outcome"]["status"] == "success"
            assert len(content_data["sections"]) == 1

            fragments_resp = await client.get("/documents/1/fragments")
            assert fragments_resp.status_code == 200
            fragments_data = fragments_resp.json()
            assert fragments_data["pipeline_outcome"]["stage"] == "fetch"
            assert fragments_data["pipeline_outcome"]["status"] == "success"
            assert fragments_data["total"] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_document_endpoints_hide_synthetic_dom_fallback_urls():
    discovered_at = datetime.now(timezone.utc)
    registry = SimpleNamespace(
        id=1,
        external_id="286_3",
        title="Synthetic DOM fallback doc",
        card_url="https://cr.minzdrav.gov.ru/clin-rec/view/286_3",
        html_url="https://cr.minzdrav.gov.ru/clin-rec/view/286_3",
        pdf_url="https://cr.minzdrav.gov.ru/clin-rec/pdf/286_3",
        specialty=None,
        age_group=None,
        status=None,
        version_label=None,
        publish_date=None,
        update_date=None,
        discovered_at=discovered_at,
        last_seen_at=discovered_at,
        source_payload_json={"id": "286_3", "title": "Synthetic DOM fallback doc", "dom_row": True},
        versions=[],
    )

    list_db = FakeAsyncSession(
        [
            FakeScalarResult(value=1),
            FakeScalarResult(values=[registry]),
        ]
    )
    detail_db = FakeAsyncSession(
        [
            FakeScalarResult(value=registry),
            FakeScalarResult(values=[]),
        ]
    )
    sessions = [list_db, detail_db]

    async def override_get_db():
        if not sessions:
            raise AssertionError("No fake session left")
        yield sessions.pop(0)

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            list_resp = await client.get("/documents")
            assert list_resp.status_code == 200
            list_item = list_resp.json()["items"][0]
            assert list_item["card_url"] is None
            assert list_item["html_url"] is None
            assert list_item["pdf_url"] is None

            detail_resp = await client.get("/documents/1")
            assert detail_resp.status_code == 200
            registry_data = detail_resp.json()["registry"]
            assert registry_data["card_url"] is None
            assert registry_data["html_url"] is None
            assert registry_data["pdf_url"] is None
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_document_artifacts_endpoint_lists_only_current_valid_artifacts(monkeypatch):
    version = SimpleNamespace(id=11)
    valid_html = SimpleNamespace(
        id=7,
        document_version_id=11,
        artifact_type="html",
        raw_path="documents/1/versions/11/html.html",
        content_hash="hash-html",
        content_type="text/html",
        fetched_at=datetime.now(timezone.utc),
    )
    invalid_pdf = SimpleNamespace(
        id=8,
        document_version_id=11,
        artifact_type="pdf",
        raw_path="documents/1/versions/11/pdf.pdf",
        content_hash="hash-pdf",
        content_type="text/html",
        fetched_at=datetime.now(timezone.utc),
    )

    db = FakeAsyncSession(
        [
            FakeScalarResult(value=version),
            FakeScalarResult(values=[valid_html, invalid_pdf]),
        ]
    )

    async def override_get_db():
        yield db

    monkeypatch.setattr(
        "app.api.documents.download_artifact",
        lambda path: b"<html><body>clinical recommendation text</body></html>"
        if path.endswith("html.html")
        else b"<!doctype html><html lang='ru'></html>",
    )

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/documents/1/artifacts")

        assert resp.status_code == 200
        data = resp.json()
        assert data["document_id"] == 1
        assert data["version_id"] == 11
        assert data["total"] == 1
        assert data["artifacts"][0]["id"] == 7
        assert data["artifacts"][0]["download_url"] == "/documents/1/artifacts/7/download"
        assert data["artifacts"][0]["preview_url"] == "/documents/1/artifacts/7/download?disposition=inline"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_document_artifact_download_endpoint_streams_valid_current_artifact(monkeypatch):
    version = SimpleNamespace(id=11)
    valid_pdf = SimpleNamespace(
        id=9,
        document_version_id=11,
        artifact_type="pdf",
        raw_path="documents/1/versions/11/pdf.pdf",
        content_hash="hash-pdf",
        content_type="application/pdf",
        fetched_at=datetime.now(timezone.utc),
    )
    pdf_bytes = b"%PDF-1.7\nraw pdf bytes"

    db = FakeAsyncSession(
        [
            FakeScalarResult(value=version),
            FakeScalarResult(values=[valid_pdf]),
        ]
    )

    async def override_get_db():
        yield db

    monkeypatch.setattr("app.api.documents.download_artifact", lambda _path: pdf_bytes)

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/documents/1/artifacts/9/download?disposition=inline")

        assert resp.status_code == 200
        assert resp.content == pdf_bytes
        assert resp.headers["content-type"].startswith("application/pdf")
        assert resp.headers["content-disposition"] == 'inline; filename="document_artifact_9.pdf"'
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_document_artifacts_route_requires_auth_header_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_key", "pilot-secret")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/documents/1/artifacts")

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid API key"


@pytest.mark.asyncio
async def test_document_artifact_download_endpoint_accepts_auth_header_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "api_auth_enabled", True)
    monkeypatch.setattr(settings, "api_key", "pilot-secret")

    version = SimpleNamespace(id=11)
    valid_html = SimpleNamespace(
        id=9,
        document_version_id=11,
        artifact_type="html",
        raw_path="documents/1/versions/11/html.html",
        content_hash="hash-html",
        content_type="text/html",
        fetched_at=datetime.now(timezone.utc),
    )

    db = FakeAsyncSession(
        [
            FakeScalarResult(value=version),
            FakeScalarResult(values=[valid_html]),
        ]
    )

    async def override_get_db():
        yield db

    monkeypatch.setattr("app.api.documents.download_artifact", lambda _path: b"<html>ok</html>")

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/documents/1/artifacts/9/download?disposition=inline",
                headers={"X-CRIN-API-Key": "pilot-secret"},
            )

        assert resp.status_code == 200
        assert resp.headers["content-disposition"] == 'inline; filename="document_artifact_9.html"'
        assert resp.content == b"<html>ok</html>"
    finally:
        app.dependency_overrides.pop(get_db, None)
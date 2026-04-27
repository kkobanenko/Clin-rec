from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import app


class FakeScalarResult:
    def __init__(self, value=None, values=None):
        self._value = value
        self._values = values or []

    def scalar_one_or_none(self):
        return self._value

    def scalars(self):
        return self

    def all(self):
        return self._values


class FakeAsyncSession:
    def __init__(self, responses):
        self._responses = list(responses)

    async def execute(self, _query):
        if not self._responses:
            raise AssertionError("Unexpected execute call")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_documents_content_includes_fragments_in_sections():
    section = SimpleNamespace(id=7, section_path="1", section_title="Intro", section_order=0)
    fragment = SimpleNamespace(
        id=13,
        section_id=7,
        fragment_order=0,
        fragment_type="paragraph",
        fragment_text="Normalized fragment text",
        stable_id="frag-1",
        source_artifact_id=None,
        source_artifact_type=None,
        source_block_id=None,
        source_path=None,
        content_kind=None,
        extraction_confidence=None,
    )
    event = SimpleNamespace(
        stage="extract",
        status="success",
        message="ok",
        detail_json={},
        created_at=datetime.now(timezone.utc),
    )

    db = FakeAsyncSession(
        [
            FakeScalarResult(value=SimpleNamespace(id=11)),
            FakeScalarResult(values=[section]),
            FakeScalarResult(values=[fragment]),
            FakeScalarResult(value=event),
        ]
    )

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/documents/1/content")
        assert response.status_code == 200
        body = response.json()
        assert body["sections"]
        assert body["sections"][0]["fragments"]
        assert body["sections"][0]["fragments"][0]["fragment_text"] == "Normalized fragment text"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_documents_content_returns_sections_with_fragments_and_traceability():
    section = SimpleNamespace(
        id=8,
        section_path="/blocks/0",
        section_title="Traceable",
        section_order=0,
        source_artifact_id=101,
        source_artifact_type="json",
        source_block_id="block-0",
        source_path="/blocks/0",
    )
    fragment = SimpleNamespace(
        id=14,
        section_id=8,
        fragment_order=0,
        fragment_type="paragraph",
        fragment_text="Traceable fragment",
        stable_id="frag-2",
        source_artifact_id=101,
        source_artifact_type="json",
        source_block_id="block-0",
        source_path="/blocks/0/rules/0",
        content_kind="text",
        extraction_confidence=0.99,
    )
    event = SimpleNamespace(
        stage="extract",
        status="success",
        message="ok",
        detail_json={},
        created_at=datetime.now(timezone.utc),
    )

    db = FakeAsyncSession(
        [
            FakeScalarResult(value=SimpleNamespace(id=12)),
            FakeScalarResult(values=[section]),
            FakeScalarResult(values=[fragment]),
            FakeScalarResult(value=event),
        ]
    )

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/documents/1/content")
        assert response.status_code == 200
        body = response.json()
        section_out = body["sections"][0]
        fragment_out = section_out["fragments"][0]
        assert section_out["source_artifact_type"] == "json"
        assert section_out["source_block_id"] == "block-0"
        assert section_out["source_path"] == "/blocks/0"
        assert fragment_out["content_kind"] == "text"
        assert fragment_out["source_artifact_type"] == "json"
        assert fragment_out["source_block_id"] == "block-0"
    finally:
        app.dependency_overrides.pop(get_db, None)
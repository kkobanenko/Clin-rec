"""Tests for GET /documents/artifact-coverage endpoint."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

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


def _make_doc(doc_id: int) -> SimpleNamespace:
    return SimpleNamespace(id=doc_id, title=f"Doc {doc_id}", external_id=f"ext_{doc_id}")


def _make_version(version_id: int, registry_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=version_id,
        registry_id=registry_id,
        is_current=True,
        detected_at=None,
    )


def _make_artifact(artifact_id: int, version_id: int, artifact_type: str = "pdf") -> SimpleNamespace:
    return SimpleNamespace(
        id=artifact_id,
        document_version_id=version_id,
        artifact_type=artifact_type,
        raw_path=f"documents/1/versions/{version_id}/{artifact_type}.{artifact_type}",
        content_hash="abc123",
        content_type="application/pdf" if artifact_type == "pdf" else "text/html",
        fetched_at=None,
    )


@pytest.mark.asyncio
async def test_artifact_coverage_returns_expected_shape():
    """Coverage endpoint returns documented shape with counts."""
    doc = _make_doc(1)
    version = _make_version(4, 1)
    artifact = _make_artifact(10, 4, "pdf")

    session = FakeAsyncSession([
        FakeScalarResult(values=[doc]),       # list docs
        FakeScalarResult(value=version),      # get current version for doc 1
        FakeScalarResult(values=[artifact]),  # get artifacts for version 4
    ])

    async def override_db():
        yield session

    valid_bytes = b"%PDF-1.4 content"
    from app.services.artifact_validation import ArtifactValidationResult

    with (
        patch("app.api.documents.download_artifact", return_value=valid_bytes),
        patch("app.api.documents.validate_artifact_payload",
              return_value=ArtifactValidationResult(is_valid=True, reason_code=None)),
        patch("app.api.documents.compute_storage_hash", return_value="abc123"),
    ):
        app.dependency_overrides[get_db] = override_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/documents/artifact-coverage")
        finally:
            app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    assert "total_documents" in data
    assert "documents_with_current_version" in data
    assert "documents_without_current_version" in data
    assert "current_versions_with_artifacts" in data
    assert "current_versions_without_artifacts" in data
    assert "artifacts_total" in data
    assert "artifacts_downloadable" in data
    assert "artifacts_failed_validation" in data
    assert "documents" in data
    assert data["total_documents"] == 1
    assert data["artifacts_total"] == 1
    assert data["artifacts_downloadable"] == 1
    assert data["artifacts_failed_validation"] == 0
    assert len(data["documents"]) == 1
    assert data["documents"][0]["document_id"] == 1
    assert data["documents"][0]["downloadable"] is True
    assert data["documents"][0]["problems"] == []


@pytest.mark.asyncio
async def test_artifact_without_storage_bytes_shows_problem():
    """Artifact that cannot be downloaded appears in problems."""
    doc = _make_doc(2)
    version = _make_version(5, 2)
    artifact = _make_artifact(20, 5, "html")

    session = FakeAsyncSession([
        FakeScalarResult(values=[doc]),
        FakeScalarResult(value=version),
        FakeScalarResult(values=[artifact]),
    ])

    async def override_db():
        yield session

    with patch("app.api.documents.download_artifact", side_effect=Exception("not found")):
        app.dependency_overrides[get_db] = override_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/documents/artifact-coverage")
        finally:
            app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["artifacts_failed_validation"] == 1
    doc_entry = data["documents"][0]
    assert doc_entry["downloadable"] is False
    assert any("storage_error" in p for p in doc_entry["problems"])


@pytest.mark.asyncio
async def test_artifact_with_hash_mismatch_shows_problem():
    """Artifact with wrong content hash appears in problems."""
    doc = _make_doc(3)
    version = _make_version(6, 3)
    artifact = _make_artifact(30, 6, "pdf")

    session = FakeAsyncSession([
        FakeScalarResult(values=[doc]),
        FakeScalarResult(value=version),
        FakeScalarResult(values=[artifact]),
    ])

    async def override_db():
        yield session

    with (
        patch("app.api.documents.download_artifact", return_value=b"%PDF-1.4 data"),
        patch("app.api.documents.compute_storage_hash", return_value="WRONG_HASH"),
    ):
        app.dependency_overrides[get_db] = override_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/documents/artifact-coverage")
        finally:
            app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    data = resp.json()
    assert data["artifacts_failed_validation"] == 1
    doc_entry = data["documents"][0]
    assert doc_entry["downloadable"] is False
    assert any("hash_mismatch" in p for p in doc_entry["problems"])


@pytest.mark.asyncio
async def test_coverage_does_not_use_external_url():
    """Coverage endpoint must not make requests to external HTML/PDF URLs."""
    import httpx
    doc = _make_doc(4)
    version = _make_version(7, 4)

    session = FakeAsyncSession([
        FakeScalarResult(values=[doc]),
        FakeScalarResult(value=version),
        FakeScalarResult(values=[]),  # no artifacts
    ])

    async def override_db():
        yield session

    with patch("httpx.Client") as mock_client, patch("httpx.AsyncClient") as mock_async_client:
        app.dependency_overrides[get_db] = override_db
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/documents/artifact-coverage")
        finally:
            app.dependency_overrides.pop(get_db, None)

        # httpx client should not have been called externally by the coverage endpoint itself
        mock_client.assert_not_called()

    assert resp.status_code == 200
    data = resp.json()
    doc_entry = data["documents"][0]
    assert "no_artifacts" in doc_entry["problems"]

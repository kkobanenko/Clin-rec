"""Справочный endpoint стадий хранения — без БД."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import app


@pytest.mark.asyncio
async def test_storage_stages_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/pipeline/storage-stages")
        assert r.status_code == 200
        data = r.json()
        assert "postgresql" in data
        assert "object_storage_s3" in data
        assert any(s.get("stage") == "fetch" for s in data["postgresql"])


@pytest.mark.asyncio
async def test_discovery_report_endpoint_exposes_stats_report():
    class _FakeScalar:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    class _FakeSession:
        async def execute(self, _query):
            return _FakeScalar(
                type(
                    "RunRow",
                    (),
                    {
                        "id": 77,
                        "stage": "discovery",
                        "status": "completed",
                        "stats_json": {
                            "discovery_strategy_report": {
                                "mode": "smoke",
                                "strategy": "playwright_fallback",
                                "completeness_claim": "smoke_only",
                            }
                        },
                    },
                )()
            )

    async def override_get_db():
        yield _FakeSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/pipeline/77/discovery-report")

        assert r.status_code == 200
        data = r.json()
        assert data["run_id"] == 77
        assert data["discovery_strategy_report"]["mode"] == "smoke"
        assert data["discovery_strategy_report"]["completeness_claim"] == "smoke_only"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_corpus_stats_endpoint_returns_expected_structure():
    """corpus-stats endpoint should return the corpus metrics structure."""

    class _FakeResult:
        def __init__(self, rows):
            self._rows = rows

        def scalar_one(self):
            return self._rows[0] if self._rows else 0

        def all(self):
            return []  # group-by queries return empty for fake session

    class _FakeSession:
        async def execute(self, _query):
            return _FakeResult([0])

    async def override_get_db():
        yield _FakeSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/pipeline/corpus-stats")

        assert r.status_code == 200
        data = r.json()
        assert "current_versions" in data
        assert "artifact_type_counts" in data
        assert "section_count" in data
        assert "content_kind_counts" in data
        assert "source_artifact_type_counts" in data
        assert "pipeline_stage_counts" in data
        assert "pair_evidence_total" in data
        assert "matrix_cell_total" in data
        assert "clinical_context_total" in data
    finally:
        app.dependency_overrides.pop(get_db, None)

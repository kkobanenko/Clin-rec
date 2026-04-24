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

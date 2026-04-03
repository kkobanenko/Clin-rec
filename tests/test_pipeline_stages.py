"""Справочный endpoint стадий хранения — без БД."""

import pytest
from httpx import ASGITransport, AsyncClient

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

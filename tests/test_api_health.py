"""Tests for FastAPI health endpoint."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import app


@pytest.mark.asyncio
async def test_full_sync_returns_task_id():
    class FakeAsyncSession:
        def __init__(self):
            self._next_id = 1

        def add(self, instance):
            instance.id = self._next_id
            self._next_id += 1

        async def flush(self):
            return None

        async def commit(self):
            return None

    fake_session = FakeAsyncSession()

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch("app.api.sync.run_full_sync.delay", return_value=SimpleNamespace(id="task-full-1")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/sync/full")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "pending"
    assert data["task_id"] == "task-full-1"
    assert data["run_id"] > 0


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

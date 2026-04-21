from types import SimpleNamespace
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import app


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class FakeRowsResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class FakeAsyncSession:
    def __init__(self, values):
        self._values = list(values)

    async def execute(self, _query):
        if not self._values:
            raise AssertionError("Unexpected execute call")
        return self._values.pop(0)


@pytest.mark.asyncio
async def test_list_outputs_returns_paginated_rows():
    async def override_get_db():
        yield FakeAsyncSession(
            [
                FakeScalarResult(1),
                FakeRowsResult(
                    [
                        SimpleNamespace(
                            id=5,
                            output_type="memo",
                            title="Demo memo",
                            artifact_id=None,
                            file_pointer=None,
                            scope_json=None,
                            generator_version="v1",
                            review_status=None,
                            released_at=None,
                            file_back_status=None,
                        )
                    ]
                ),
            ]
        )

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs?page=1&page_size=50")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Demo memo"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_output_returns_row():
    async def override_get_db():
        yield FakeAsyncSession(
            [
                FakeScalarResult(
                    SimpleNamespace(
                        id=5,
                        output_type="memo",
                        title="Demo memo",
                        artifact_id=None,
                        file_pointer=None,
                        scope_json=None,
                        generator_version="v1",
                        review_status=None,
                        released_at=None,
                        file_back_status=None,
                    )
                )
            ]
        )

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs/5")

        assert resp.status_code == 200
        assert resp.json()["id"] == 5
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_generate_output_queues_task():
    task = SimpleNamespace(id="task-123")
    with patch("app.api.outputs.generate_outputs_task.delay", return_value=task):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/outputs/generate",
                json={"output_type": "memo", "title": "Demo memo", "scope_json": None},
            )

    assert resp.status_code == 202
    data = resp.json()
    assert data["task_id"] == "task-123"
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_file_back_alias_queues_task():
    task = SimpleNamespace(id="task-456")
    with patch("app.api.outputs.file_outputs_task.delay", return_value=task):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/outputs/file-back/5",
                json={"file_back_status": "accepted"},
            )

    assert resp.status_code == 202
    data = resp.json()
    assert data["task_id"] == "task-456"
    assert data["output_id"] == 5
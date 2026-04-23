from types import SimpleNamespace
from unittest.mock import patch
from datetime import datetime, timezone

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
        self.queries = []

    async def execute(self, query):
        self.queries.append(query)
        if not self._values:
            raise AssertionError("Unexpected execute call")
        return self._values.pop(0)


@pytest.mark.asyncio
async def test_list_outputs_returns_paginated_rows():
    fake_session = FakeAsyncSession(
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

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs?page=1&page_size=50")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Demo memo"
        assert len(fake_session.queries) == 2
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_outputs_applies_file_back_and_search_filters():
    fake_session = FakeAsyncSession(
        [
            FakeScalarResult(1),
            FakeRowsResult(
                [
                    SimpleNamespace(
                        id=9,
                        output_type="memo",
                        title="Accepted insulin memo",
                        artifact_id=3,
                        file_pointer="var/crin_outputs/accepted-insulin.md",
                        scope_json=None,
                        generator_version="v2",
                        review_status=None,
                        released_at=None,
                        file_back_status="accepted",
                    )
                ]
            ),
        ]
    )

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/outputs?page=1&page_size=50&output_type=memo&file_back_status=accepted&search=insulin"
            )

        assert resp.status_code == 200
        compiled_count = fake_session.queries[0].compile()
        compiled_rows = fake_session.queries[1].compile()
        for compiled in (compiled_count, compiled_rows):
            sql = str(compiled)
            params = compiled.params
            assert "output_release.output_type = :output_type_1" in sql
            assert "output_release.file_back_status = :file_back_status_1" in sql
            assert "lower(output_release.title) LIKE lower(:title_1)" in sql
            assert params["output_type_1"] == "memo"
            assert params["file_back_status_1"] == "accepted"
        assert compiled_count.params["title_1"] == "%insulin%"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_outputs_applies_review_status_filter():
    fake_session = FakeAsyncSession(
        [
            FakeScalarResult(1),
            FakeRowsResult(
                [
                    SimpleNamespace(
                        id=11,
                        output_type="memo",
                        title="Needs review memo",
                        artifact_id=7,
                        file_pointer="var/crin_outputs/review-memo.md",
                        scope_json=None,
                        generator_version="v2",
                        review_status="needs_review",
                        released_at=None,
                        file_back_status="accepted",
                    )
                ]
            ),
        ]
    )

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs?page=1&page_size=50&review_status=needs_review")

        assert resp.status_code == 200
        compiled_count = fake_session.queries[0].compile()
        compiled_rows = fake_session.queries[1].compile()
        for compiled in (compiled_count, compiled_rows):
            sql = str(compiled)
            params = compiled.params
            assert "output_release.review_status = :review_status_1" in sql
            assert params["review_status_1"] == "needs_review"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_outputs_applies_released_only_filter():
    fake_session = FakeAsyncSession(
        [
            FakeScalarResult(1),
            FakeRowsResult(
                [
                    SimpleNamespace(
                        id=12,
                        output_type="memo",
                        title="Released memo",
                        artifact_id=8,
                        file_pointer="var/crin_outputs/released-memo.md",
                        scope_json=None,
                        generator_version="v2",
                        review_status="approved",
                        released_at=datetime.now(timezone.utc),
                        file_back_status="accepted",
                    )
                ]
            ),
        ]
    )

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs?page=1&page_size=50&released_only=true")

        assert resp.status_code == 200
        compiled_count = fake_session.queries[0].compile()
        compiled_rows = fake_session.queries[1].compile()
        for compiled in (compiled_count, compiled_rows):
            sql = str(compiled)
            assert "output_release.released_at IS NOT NULL" in sql
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_outputs_applies_artifact_filter():
    fake_session = FakeAsyncSession(
        [
            FakeScalarResult(1),
            FakeRowsResult(
                [
                    SimpleNamespace(
                        id=10,
                        output_type="memo",
                        title="Artifact linked memo",
                        artifact_id=55,
                        file_pointer="var/crin_outputs/artifact-linked.md",
                        scope_json=None,
                        generator_version="v2",
                        review_status=None,
                        released_at=None,
                        file_back_status="accepted",
                    )
                ]
            ),
        ]
    )

    async def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs?page=1&page_size=50&artifact_id=55")

        assert resp.status_code == 200
        compiled_count = fake_session.queries[0].compile()
        compiled_rows = fake_session.queries[1].compile()
        for compiled in (compiled_count, compiled_rows):
            sql = str(compiled)
            params = compiled.params
            assert "output_release.artifact_id = :artifact_id_1" in sql
            assert params["artifact_id_1"] == 55
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
async def test_get_output_returns_404_when_missing():
    async def override_get_db():
        yield FakeAsyncSession([FakeScalarResult(None)])

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/outputs/999")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Output not found"
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
async def test_generate_memo_alias_queues_memo_task():
    task = SimpleNamespace(id="task-234")
    with patch("app.api.outputs.generate_outputs_task.delay", return_value=task) as mocked_delay:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/outputs/memo",
                json={"title": "Memo title", "scope_json": None},
            )

    assert resp.status_code == 202
    mocked_delay.assert_called_once_with(output_type="memo", title="Memo title", scope_json=None)
    assert resp.json()["output_type"] == "memo"


@pytest.mark.asyncio
async def test_file_output_queues_task():
    task = SimpleNamespace(id="task-345")
    with patch("app.api.outputs.file_outputs_task.delay", return_value=task):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/outputs/file",
                json={"output_id": 5, "file_back_status": "accepted"},
            )

    assert resp.status_code == 202
    data = resp.json()
    assert data["task_id"] == "task-345"
    assert data["output_id"] == 5


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
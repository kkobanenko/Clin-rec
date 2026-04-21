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
async def test_create_review_action_uses_reviewer_service_approve():
    action = SimpleNamespace(
        id=1,
        target_type="pair_evidence",
        target_id=7,
        action="approve",
        old_value_json={"review_status": "auto"},
        new_value_json={"review_status": "approved"},
        reason=None,
        author="tester",
        created_at="2026-04-21T00:00:00Z",
    )

    with patch("app.api.pipeline.ReviewerService.approve", return_value=action):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/review",
                json={
                    "target_type": "pair_evidence",
                    "target_id": 7,
                    "action": "approve",
                    "author": "tester",
                },
            )

    assert resp.status_code == 200
    assert resp.json()["action"] == "approve"


@pytest.mark.asyncio
async def test_get_review_queue_returns_paginated_evidence():
    async def override_get_db():
        yield FakeAsyncSession([FakeScalarResult(2)])

    app.dependency_overrides[get_db] = override_get_db
    evidence = [
        SimpleNamespace(
            id=1,
            context_id=10,
            molecule_from_id=7,
            molecule_to_id=5,
            fragment_id=11,
            relation_type="no_substitution_signal",
            uur=None,
            udd=None,
            role_score=0.5,
            text_score=0.5,
            population_score=0.5,
            parity_score=0.5,
            practical_score=0.5,
            penalty=0.0,
            final_fragment_score=0.5,
            review_status="auto",
            created_at="2026-04-21T00:00:00Z",
        )
    ]

    try:
        with patch("app.api.pipeline.ReviewerService.get_review_queue", return_value=evidence):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/review/queue?status=auto&page=1&page_size=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["items"][0]["review_status"] == "auto"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_review_queue_passes_document_version_filter():
    async def override_get_db():
        yield FakeAsyncSession([FakeScalarResult(1)])

    app.dependency_overrides[get_db] = override_get_db
    evidence = [
        SimpleNamespace(
            id=1,
            context_id=10,
            molecule_from_id=7,
            molecule_to_id=5,
            fragment_id=11,
            relation_type="no_substitution_signal",
            uur=None,
            udd=None,
            role_score=0.5,
            text_score=0.5,
            population_score=0.5,
            parity_score=0.5,
            practical_score=0.5,
            penalty=0.0,
            final_fragment_score=0.5,
            review_status="auto",
            created_at="2026-04-21T00:00:00Z",
        )
    ]

    try:
        with patch("app.api.pipeline.ReviewerService.get_review_queue", return_value=evidence) as mocked_queue:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/review/queue?status=auto&document_version_id=4&page=1&page_size=20")

        assert resp.status_code == 200
        mocked_queue.assert_called_once_with(status="auto", limit=20, offset=0, document_version_id=4)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_review_stats_returns_aggregated_counts():
    with patch("app.api.pipeline.ReviewerService.get_review_stats", return_value={"auto": 3, "approved": 2}):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/review/stats")

    assert resp.status_code == 200
    data = resp.json()
    assert data["counts"]["auto"] == 3
    assert data["total"] == 5


@pytest.mark.asyncio
async def test_bulk_approve_reviews_returns_count():
    with patch("app.api.pipeline.ReviewerService.bulk_approve", return_value=3):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/review/bulk-approve",
                json={"evidence_ids": [1, 2, 3, 4], "author": "tester"},
            )

    assert resp.status_code == 200
    assert resp.json()["approved_count"] == 3


@pytest.mark.asyncio
async def test_get_review_history_returns_paginated_actions():
    async def override_get_db():
        yield FakeAsyncSession([FakeScalarResult(1)])

    app.dependency_overrides[get_db] = override_get_db
    actions = [
        SimpleNamespace(
            id=1,
            target_type="pair_evidence",
            target_id=7,
            action="reject",
            old_value_json={"review_status": "auto"},
            new_value_json={"review_status": "rejected"},
            reason="weak evidence",
            author="tester",
            created_at="2026-04-21T00:00:00Z",
        )
    ]

    try:
        with patch("app.api.pipeline.ReviewerService.get_review_history", return_value=actions):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/review/history?page=1&page_size=20")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["action"] == "reject"
    finally:
        app.dependency_overrides.pop(get_db, None)
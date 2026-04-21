from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import app


@pytest.mark.asyncio
async def test_get_model_readiness_returns_service_payload():
    readiness = {
        "ready": True,
        "has_matrix_cells": True,
        "sufficient_evidence": True,
        "low_confidence_acceptable": True,
        "cell_count": 12,
        "pcs_count": 14,
        "low_confidence_ratio": 0.1,
    }

    with patch("app.api.matrix.ReleaseService.check_readiness", return_value=readiness):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/matrix/models/7/readiness")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ready"] is True
    assert data["cell_count"] == 12


@pytest.mark.asyncio
async def test_get_active_model_returns_latest_active_model():
    class FakeScalarResult:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    class FakeAsyncSession:
        async def execute(self, _query):
            from types import SimpleNamespace

            return FakeScalarResult(
                SimpleNamespace(
                    id=7,
                    version_label="v-test",
                    weights_json={"base": 1.0},
                    code_commit_hash="abc123",
                    description="active model",
                    is_active=True,
                    created_at="2026-04-21T00:00:00Z",
                )
            )

    async def override_get_db():
        yield FakeAsyncSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/matrix/models/active")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 7
        assert data["is_active"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_get_model_overview_returns_release_summaries():
    class FakeRowsResult:
        def __init__(self, rows):
            self._rows = rows

        def scalars(self):
            return self

        def all(self):
            return self._rows

    class FakeAsyncSession:
        async def execute(self, _query):
            from types import SimpleNamespace

            return FakeRowsResult(
                [
                    SimpleNamespace(id=7, version_label="v-test", is_active=True),
                    SimpleNamespace(id=6, version_label="v-prev", is_active=False),
                ]
            )

    async def override_get_db():
        yield FakeAsyncSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch(
            "app.api.matrix.ReleaseService.check_readiness",
            side_effect=[
                {"ready": True, "cell_count": 12, "pcs_count": 14},
                {"ready": False, "cell_count": 0, "pcs_count": 0},
            ],
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/matrix/models/overview")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["model_version_id"] == 7
        assert data[0]["readiness"]["ready"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_activate_model_returns_activation_payload():
    activation = {
        "model_version_id": 7,
        "version_label": "v-test",
        "released_by": "tester",
        "forced": False,
        "readiness": {
            "ready": True,
            "has_matrix_cells": True,
            "sufficient_evidence": True,
            "low_confidence_acceptable": True,
            "cell_count": 12,
            "pcs_count": 14,
            "low_confidence_ratio": 0.1,
        },
    }

    with patch("app.api.matrix.ReleaseService.create_release", return_value=activation):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/matrix/models/7/activate", json={"author": "tester", "force": False})

    assert resp.status_code == 200
    data = resp.json()
    assert data["model_version_id"] == 7
    assert data["readiness"]["ready"] is True


@pytest.mark.asyncio
async def test_activate_model_returns_conflict_when_not_ready():
    with patch("app.api.matrix.ReleaseService.create_release", return_value=None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/matrix/models/7/activate", json={"author": "tester", "force": False})

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_refresh_model_returns_score_and_matrix_counts():
    with (
        patch("app.api.matrix.ScoringEngine.score_all", return_value=9),
        patch("app.api.matrix.MatrixBuilder.build", return_value=5),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/matrix/models/7/refresh",
                json={"scope_type": "global", "scope_id": None},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["model_version_id"] == 7
    assert data["pair_context_scores"] == 9
    assert data["matrix_cells"] == 5


@pytest.mark.asyncio
async def test_get_model_summary_returns_model_and_readiness():
    class FakeScalarResult:
        def __init__(self, value):
            self._value = value

        def scalar_one_or_none(self):
            return self._value

    class FakeAsyncSession:
        async def execute(self, _query):
            from types import SimpleNamespace

            return FakeScalarResult(SimpleNamespace(id=7, version_label="v-test", is_active=True))

    async def override_get_db():
        yield FakeAsyncSession()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with patch(
            "app.api.matrix.ReleaseService.check_readiness",
            return_value={"ready": True, "cell_count": 12, "pcs_count": 14},
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/matrix/models/7/summary")

        assert resp.status_code == 200
        data = resp.json()
        assert data["model_version_id"] == 7
        assert data["is_active"] is True
        assert data["readiness"]["ready"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_diff_models_returns_service_payload():
    diff = {
        "old_version_id": 1,
        "new_version_id": 2,
        "added": 1,
        "removed": 0,
        "changed": 1,
        "details": {
            "added": [{"from": 1, "to": 2, "scope_type": "global", "scope_id": None, "score": 0.7}],
            "removed": [],
            "changed": [{"from": 1, "to": 3, "scope_type": "global", "scope_id": None, "old_score": 0.4, "new_score": 0.8, "delta": 0.4}],
        },
    }

    with patch("app.api.matrix.ReleaseService.diff_versions", return_value=diff):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/matrix/models/diff?old_version_id=1&new_version_id=2")

    assert resp.status_code == 200
    data = resp.json()
    assert data["added"] == 1
    assert data["details"]["added"][0]["from_"] == 1
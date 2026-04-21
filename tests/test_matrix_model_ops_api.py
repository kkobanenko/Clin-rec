from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

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
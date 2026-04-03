"""GET /matrix/pair-evidence: контракт ответа без реальной БД (mock AsyncSession)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.dependencies import get_db
from app.main import app


@pytest.mark.asyncio
async def test_pair_evidence_list_empty():
    mock_session = MagicMock()
    r_count = MagicMock()
    r_count.scalar_one.return_value = 0
    r_rows = MagicMock()
    r_rows.scalars.return_value.all.return_value = []
    mock_session.execute = AsyncMock(side_effect=[r_count, r_rows])

    async def _db():
        yield mock_session

    app.dependency_overrides[get_db] = _db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/matrix/pair-evidence?page=1&page_size=10")
            assert resp.status_code == 200
            data = resp.json()
            assert data["items"] == []
            assert data["total"] == 0
            assert data["page"] == 1
            assert data["page_size"] == 10
    finally:
        app.dependency_overrides.pop(get_db, None)

import pytest
from httpx import ASGITransport, AsyncClient
from datetime import datetime, timezone

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
    def __init__(self, values, assertions):
        self._values = list(values)
        self._assertions = list(assertions)

    async def execute(self, query):
        if self._assertions:
            self._assertions.pop(0)(query)
        if not self._values:
            raise AssertionError("Unexpected execute call")
        return self._values.pop(0)


NOW = datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_list_claims_filters_by_type_and_search():
    def assert_count_query(query):
        compiled = query.compile()
        sql = str(compiled)
        params = compiled.params
        assert "knowledge_claim.artifact_id = :artifact_id_1" in sql
        assert "knowledge_claim.claim_type = :claim_type_1" in sql
        assert "lower(knowledge_claim.claim_text) LIKE lower(:claim_text_1)" in sql
        assert params["artifact_id_1"] == 7
        assert params["claim_type_1"] == "fact"
        assert params["claim_text_1"] == "%insulin%"

    def assert_rows_query(query):
        compiled = query.compile()
        sql = str(compiled)
        assert "ORDER BY knowledge_claim.id" in sql

    fake_db = FakeAsyncSession(
        values=[
            FakeScalarResult(1),
            FakeRowsResult(
                [
                    type(
                        "ClaimRow",
                        (),
                        {
                            "id": 11,
                            "artifact_id": 7,
                            "claim_type": "fact",
                            "claim_text": "Insulin recommended for severe diabetes",
                            "confidence": "medium",
                            "review_status": "auto",
                            "conflict_group_id": None,
                            "is_conflicted": False,
                            "created_at": NOW,
                            "updated_at": NOW,
                        },
                    )()
                ]
            ),
        ],
        assertions=[assert_count_query, assert_rows_query],
    )

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/kb/claims?artifact_id=7&claim_type=fact&search=insulin&page=1&page_size=50"
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["claim_type"] == "fact"
        assert "Insulin" in data["items"][0]["claim_text"]
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_claims_returns_multiple_types_without_filters():
    def assert_count_query(query):
        compiled = query.compile()
        sql = str(compiled)
        params = compiled.params
        assert "knowledge_claim.artifact_id = :artifact_id_1" in sql
        assert "claim_type" not in params
        assert "claim_text_1" not in params

    fake_db = FakeAsyncSession(
        values=[
            FakeScalarResult(2),
            FakeRowsResult(
                [
                    type(
                        "ClaimRow",
                        (),
                        {
                            "id": 21,
                            "artifact_id": 9,
                            "claim_type": "fact",
                            "claim_text": "First claim",
                            "confidence": "medium",
                            "review_status": "auto",
                            "conflict_group_id": None,
                            "is_conflicted": False,
                            "created_at": NOW,
                            "updated_at": NOW,
                        },
                    )(),
                    type(
                        "ClaimRow",
                        (),
                        {
                            "id": 22,
                            "artifact_id": 9,
                            "claim_type": "hypothesis",
                            "claim_text": "Second claim",
                            "confidence": "low",
                            "review_status": "needs_review",
                            "conflict_group_id": None,
                            "is_conflicted": False,
                            "created_at": NOW,
                            "updated_at": NOW,
                        },
                    )(),
                ]
            ),
        ],
        assertions=[assert_count_query, lambda _query: None],
    )

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/kb/claims?artifact_id=9&page=1&page_size=50")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert {item["claim_type"] for item in data["items"]} == {"fact", "hypothesis"}
    finally:
        app.dependency_overrides.pop(get_db, None)
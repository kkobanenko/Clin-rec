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


class FakeArtifactRowsResult(FakeRowsResult):
    pass


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
        assert "knowledge_claim.review_status = :review_status_1" in sql
        assert "knowledge_claim.is_conflicted IS true" in sql
        assert "lower(knowledge_claim.claim_text) LIKE lower(:claim_text_1)" in sql
        assert params["artifact_id_1"] == 7
        assert params["claim_type_1"] == "fact"
        assert params["review_status_1"] == "auto"
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
                            "is_conflicted": True,
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
                "/kb/claims?artifact_id=7&claim_type=fact&review_status=auto&conflicted_only=true&search=insulin&page=1&page_size=50"
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["claim_type"] == "fact"
        assert data["items"][0]["is_conflicted"] is True
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


@pytest.mark.asyncio
async def test_list_artifacts_filters_by_type_status_and_search():
    def assert_count_query(query):
        compiled = query.compile()
        sql = str(compiled)
        params = compiled.params
        assert "knowledge_artifact.artifact_type = :artifact_type_1" in sql
        assert "knowledge_artifact.status = :status_1" in sql
        assert "knowledge_artifact.review_status = :review_status_1" in sql
        assert "knowledge_artifact.generator_version = :generator_version_1" in sql
        assert "lower(knowledge_artifact.title) LIKE lower(:title_1)" in sql
        assert "lower(knowledge_artifact.content_md) LIKE lower(:content_md_1)" in sql
        assert params["artifact_type_1"] == "source_digest"
        assert params["status_1"] == "draft"
        assert params["review_status_1"] == "needs_review"
        assert params["generator_version_1"] == "0.3.0"
        assert params["title_1"] == "%digest%"
        assert params["content_md_1"] == "%digest%"

    fake_db = FakeAsyncSession(
        values=[
            FakeScalarResult(1),
            FakeArtifactRowsResult(
                [
                    type(
                        "ArtifactRow",
                        (),
                        {
                            "id": 31,
                            "artifact_type": "source_digest",
                            "title": "Digest artifact",
                            "canonical_slug": "digest/v31",
                            "status": "draft",
                            "summary": "Digest summary",
                            "confidence": None,
                            "review_status": "needs_review",
                            "generator_version": "0.3.0",
                            "created_at": NOW,
                            "updated_at": NOW,
                        },
                    )()
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
            resp = await client.get(
                "/kb/artifacts?page=1&page_size=50&artifact_type=source_digest&status=draft&review_status=needs_review&generator_version=0.3.0&search=digest"
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["canonical_slug"] == "digest/v31"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_entities_filters_by_type_status_and_search():
    def assert_count_query(query):
        compiled = query.compile()
        sql = str(compiled)
        params = compiled.params
        assert "entity_registry.entity_type = :entity_type_1" in sql
        assert "entity_registry.status = :status_1" in sql
        assert "lower(entity_registry.canonical_name) LIKE lower(:canonical_name_1)" in sql
        assert "CAST(entity_registry.aliases_json AS TEXT)" in sql
        assert "CAST(entity_registry.external_refs_json AS TEXT)" in sql
        assert params["entity_type_1"] == "molecule"
        assert params["status_1"] == "active"
        assert params["canonical_name_1"] == "%insulin%"

    fake_db = FakeAsyncSession(
        values=[
            FakeScalarResult(1),
            FakeRowsResult(
                [
                    type(
                        "EntityRow",
                        (),
                        {
                            "id": 41,
                            "entity_type": "molecule",
                            "canonical_name": "Insulin",
                            "aliases_json": None,
                            "external_refs_json": {"molecule_id": 5},
                            "status": "active",
                        },
                    )()
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
            resp = await client.get(
                "/kb/entities?page=1&page_size=50&entity_type=molecule&status=active&search=insulin"
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["canonical_name"] == "Insulin"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_list_conflicts_returns_counts_and_previews():
    def assert_conflicts_query(query):
        compiled = query.compile()
        sql = str(compiled)
        params = compiled.params
        assert "knowledge_claim.conflict_group_id IS NOT NULL" in sql
        assert "knowledge_claim.artifact_id = :artifact_id_1" in sql
        assert params["artifact_id_1"] == 7

    fake_db = FakeAsyncSession(
        values=[
            FakeRowsResult(
                [
                    type(
                        "ClaimRow",
                        (),
                        {
                            "id": 51,
                            "artifact_id": 7,
                            "conflict_group_id": 9,
                            "claim_text": "Insulin should be first-line therapy in this scenario.",
                        },
                    )(),
                    type(
                        "ClaimRow",
                        (),
                        {
                            "id": 52,
                            "artifact_id": 7,
                            "conflict_group_id": 9,
                            "claim_text": "Insulin should be reserved for rescue therapy in this scenario.",
                        },
                    )(),
                ]
            )
        ],
        assertions=[assert_conflicts_query],
    )

    async def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/kb/conflicts?artifact_id=7")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["conflict_group_id"] == 9
        assert data[0]["claim_count"] == 2
        assert data[0]["artifact_ids"] == [7]
        assert data[0]["claim_ids"] == [51, 52]
        assert any("first-line therapy" in preview for preview in data[0]["claim_previews"])
    finally:
        app.dependency_overrides.pop(get_db, None)
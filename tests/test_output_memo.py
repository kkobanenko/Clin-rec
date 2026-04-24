"""Юнит-тесты генерации memo без БД (ветка scope_json.digest_slugs)."""

from types import SimpleNamespace

from app.services.output_release_service import _build_memo_markdown
from app.services.output_release_service import apply_file_back


def test_build_memo_with_explicit_slugs():
    class _NoDb:
        def execute(self, _q):
            raise AssertionError("не должны ходить в БД при переданных digest_slugs")

    body, manifest = _build_memo_markdown(_NoDb(), 42, {"digest_slugs": ["digest/v7", "digest/v8"]})
    assert body.startswith("---\n")
    assert "review_status: pending_review" in body
    assert "Internal analytical draft. Not a medical recommendation." in body
    assert "Requires human review before release." in body
    assert "[[digest/v7]]" in body
    assert "[[digest/v8]]" in body
    assert manifest["digest_slugs"] == ["digest/v7", "digest/v8"]


def test_apply_file_back_creates_artifact_for_accepted_output(monkeypatch):
    row = SimpleNamespace(
        id=42,
        output_type="memo",
        title="Demo memo",
        artifact_id=None,
        file_pointer="/tmp/memo_42.md",
        review_status="pending_review",
        generator_version="0.2.0",
        released_at=None,
        file_back_status="pending",
    )

    class _Session:
        def __init__(self):
            self.next_artifact_id = 500
            self.added = []

        def get(self, model, object_id):
            return row if object_id == 42 else None

        def add(self, obj):
            if getattr(obj, "id", None) is None:
                obj.id = self.next_artifact_id
            self.added.append(obj)

        def flush(self):
            return None

        def commit(self):
            return None

        def rollback(self):
            return None

        def close(self):
            return None

    session = _Session()
    monkeypatch.setattr("app.services.output_release_service.get_sync_session", lambda: session)

    result = apply_file_back(42, "accepted")

    assert result["status"] == "ok"
    assert result["artifact_created"] is True
    assert result["artifact_id"] == 500
    assert row.artifact_id == 500
    assert row.review_status == "approved"


def test_apply_file_back_skips_artifact_when_output_has_no_file(monkeypatch):
    row = SimpleNamespace(
        id=43,
        output_type="memo",
        title="Draft memo",
        artifact_id=None,
        file_pointer=None,
        review_status="pending_review",
        generator_version="0.2.0",
        released_at=None,
        file_back_status="pending",
    )

    class _Session:
        def get(self, model, object_id):
            return row if object_id == 43 else None

        def add(self, obj):
            raise AssertionError("artifact must not be created without file_pointer")

        def flush(self):
            return None

        def commit(self):
            return None

        def rollback(self):
            return None

        def close(self):
            return None

    monkeypatch.setattr("app.services.output_release_service.get_sync_session", lambda: _Session())

    result = apply_file_back(43, "accepted")

    assert result["artifact_created"] is False
    assert result["artifact_id"] is None

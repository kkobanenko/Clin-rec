"""Юнит-тесты генерации memo без БД (ветка scope_json.digest_slugs)."""

from app.services.output_release_service import _build_memo_markdown


def test_build_memo_with_explicit_slugs():
    class _NoDb:
        def execute(self, _q):
            raise AssertionError("не должны ходить в БД при переданных digest_slugs")

    body, manifest = _build_memo_markdown(_NoDb(), 42, {"digest_slugs": ["digest/v7", "digest/v8"]})
    assert "[[digest/v7]]" in body
    assert "[[digest/v8]]" in body
    assert manifest["digest_slugs"] == ["digest/v7", "digest/v8"]

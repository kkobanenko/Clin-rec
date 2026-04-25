"""Тесты правил валидации байтов артефактов (html/pdf)."""

from app.services.artifact_validation import (
    is_valid_artifact_payload,
    is_valid_html_payload,
    is_valid_pdf_payload,
    looks_like_spa_shell,
)


def test_pdf_valid():
    data = b"%PDF-1.4\n%..."
    assert is_valid_pdf_payload("application/pdf", data) is True
    assert is_valid_artifact_payload("pdf", "application/pdf", data) is True


def test_pdf_rejects_html_disguise():
    data = b"<!doctype html><html></html>"
    assert is_valid_pdf_payload("application/pdf", data) is False
    assert is_valid_artifact_payload("pdf", "text/html", data) is False


def test_spa_shell_detected():
    shell = b"""<!doctype html><html><body><div id="app"></div>
<script type="module" src="/assets/index-ABC.js"></script></body></html>"""
    assert looks_like_spa_shell(shell) is True


def test_html_rejects_shell_even_with_text_html_ct():
    shell = b"""<!doctype html><html><body><div id="app"></div>
<script src="/assets/index-ABC.js"></script></body></html>"""
    assert is_valid_html_payload("text/html", shell) is False
    assert is_valid_artifact_payload("html", "text/html", shell) is False


def test_html_accepts_substantial_main():
    page = b"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body><main>
<h1>Title</h1><p>""" + (b"x" * 400) + b"""</p></main></body></html>"""
    assert looks_like_spa_shell(page) is False
    assert is_valid_html_payload("text/html", page) is True


def test_large_dom_with_app_and_assets_not_shell():
    """Большой HTML с реальным текстом не должен считаться shell."""
    padding = "x" * 3200
    page = f"""<!doctype html><html><body><div id="app"></div>
<p>{padding}</p><script type="module" src="/assets/index-ABC.js"></script></body></html>"""
    data = page.encode("utf-8")
    assert len(data) >= 3000
    assert looks_like_spa_shell(data) is False
    assert is_valid_html_payload("text/html", data) is True


def test_large_empty_shell_with_bundle_is_rejected():
    shell = b"""<!doctype html><html lang=\"ru\"><head><title>undefined</title></head><body><div id=\"app\"></div>
<script type=\"module\" src=\"/assets/index-ABC.js\"></script>
<style>""" + (b"x" * 14000) + b"""</style></body></html>"""
    assert len(shell) >= 3000
    assert looks_like_spa_shell(shell) is True
    assert is_valid_html_payload("text/html", shell) is False

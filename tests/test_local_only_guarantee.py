from types import SimpleNamespace

from app.services.normalize import NormalizeService
from app.ui.app import fetch_artifact_bytes


def test_preview_download_use_local_backend_endpoint(monkeypatch):
    captured = {}

    class _Response:
        status_code = 200
        content = b"{}"
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

    def fake_get(url, *, headers, timeout):
        captured["url"] = url
        return _Response()

    monkeypatch.setattr("app.ui.app.httpx.get", fake_get)
    result = fetch_artifact_bytes(
        {
            "artifact_type": "json",
            "download_url": "/documents/1/artifacts/1/download",
        }
    )

    assert result["ok"] is True
    assert captured["url"].startswith("http://app:8000/documents/")


def test_fetch_artifact_bytes_never_uses_external_card_html_pdf_urls(monkeypatch):
    captured = {}

    class _Response:
        status_code = 200
        content = b"{}"
        headers = {"content-type": "application/json"}

        def raise_for_status(self):
            return None

    def fake_get(url, *, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setenv("CRIN_API_KEY", "pilot-key")
    monkeypatch.setattr("app.ui.app.httpx.get", fake_get)
    result = fetch_artifact_bytes(
        {
            "artifact_type": "json",
            "download_url": "/documents/2/artifacts/7/download",
            "card_url": "https://cr.minzdrav.gov.ru/view-cr/286_3",
            "html_url": "https://cr.minzdrav.gov.ru/view-cr/286_3",
            "pdf_url": "https://cr.minzdrav.gov.ru/preview-cr/286_3",
        }
    )

    assert result["ok"] is True
    assert captured["url"] == "http://app:8000/documents/2/artifacts/7/download"
    assert captured["headers"] == {"X-CRIN-API-Key": "pilot-key"}


def test_normalize_current_version_does_not_require_external_http(monkeypatch):
    # If normalize performed external HTTP calls, this monkeypatch would fail the test.
    monkeypatch.setattr("httpx.Client.get", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("external call")))

    service = NormalizeService()
    version = SimpleNamespace(id=1, source_type_primary="html+pdf")
    html_artifact = SimpleNamespace(id=10, raw_path="html")

    monkeypatch.setattr("app.services.normalize.download_artifact", lambda _path: b"<html><body><h1>T</h1></body></html>")
    monkeypatch.setattr(service, "_normalize_html", lambda _raw: [("Intro", "1", [("paragraph", "text")])])

    result = service._extract_sections_detailed(version, None, html_artifact, None)
    assert result.sections
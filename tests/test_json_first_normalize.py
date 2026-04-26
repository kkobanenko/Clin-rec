from types import SimpleNamespace

from app.services.normalize import NormalizeService


def test_json_source_is_preferred_over_html_pdf(monkeypatch):
    service = NormalizeService()
    version = SimpleNamespace(id=42, source_type_primary="html+pdf")
    json_artifact = SimpleNamespace(id=1, raw_path="json")
    html_artifact = SimpleNamespace(id=2, raw_path="html")
    pdf_artifact = SimpleNamespace(id=3, raw_path="pdf")

    monkeypatch.setattr("app.services.normalize.download_artifact", lambda path: b'{"title":"A","rules":["1","x"]}')
    monkeypatch.setattr(service, "_normalize_html", lambda raw_data: [("HTML", "1", [("paragraph", "html")])])
    monkeypatch.setattr(service, "_normalize_pdf", lambda raw_data: [("PDF", "1", [("paragraph", "pdf")])])

    result = service._extract_sections_detailed(version, json_artifact, html_artifact, pdf_artifact)

    assert result.source_used == "json"
    assert result.source_artifact_type == "json"
    assert result.sections


def test_broken_json_falls_back_to_html(monkeypatch):
    service = NormalizeService()
    version = SimpleNamespace(id=43, source_type_primary="html+pdf")
    json_artifact = SimpleNamespace(id=1, raw_path="json")
    html_artifact = SimpleNamespace(id=2, raw_path="html")
    pdf_artifact = SimpleNamespace(id=3, raw_path="pdf")

    def fake_download(path: str) -> bytes:
        if path == "json":
            return b"{invalid json}"
        if path == "html":
            return b"<html><body><h1>T</h1><p>X</p></body></html>"
        return b"%PDF-1.4"

    monkeypatch.setattr("app.services.normalize.download_artifact", fake_download)
    monkeypatch.setattr(service, "_normalize_html", lambda raw_data: [("HTML", "1", [("paragraph", "html")])])

    result = service._extract_sections_detailed(version, json_artifact, html_artifact, pdf_artifact)

    assert result.source_used == "html_fallback"
    assert result.source_artifact_type == "html"
    assert result.sections
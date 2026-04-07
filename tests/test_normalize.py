from types import SimpleNamespace

from app.services.normalize import NormalizeService


def test_extract_sections_falls_back_to_pdf_when_html_has_no_sections(monkeypatch):
    service = NormalizeService()
    version = SimpleNamespace(id=42, source_type_primary="html+pdf")
    html_artifact = SimpleNamespace(raw_path="documents/test/html.html")
    pdf_artifact = SimpleNamespace(raw_path="documents/test/pdf.pdf")

    monkeypatch.setattr("app.services.normalize.download_artifact", lambda path: path.encode())
    monkeypatch.setattr(service, "_normalize_html", lambda raw_data: [])
    monkeypatch.setattr(service, "_normalize_html_loose", lambda raw_data: [])
    monkeypatch.setattr(service, "_normalize_html_playwright", lambda url: [])
    monkeypatch.setattr(
        service,
        "_normalize_pdf",
        lambda raw_data: [("Документ", "0", [("paragraph", "Normalized from PDF")])],
    )

    sections = service._extract_sections(version, html_artifact, pdf_artifact, None)

    assert sections == [("Документ", "0", [("paragraph", "Normalized from PDF")])]



from app.services.artifact_validation import is_valid_artifact_payload
from app.services.probe import ProbeService


class DummyResponse:
    def __init__(self, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


class DummyClient:
    def __init__(self, response):
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def head(self, url):
        return self.response


def test_probe_rejects_html_response_for_pdf(monkeypatch):
    response = DummyResponse(status_code=200, headers={"content-type": "text/html"})
    monkeypatch.setattr("app.services.probe.httpx.Client", lambda **kwargs: DummyClient(response))

    service = ProbeService()

    assert service._check_url("https://example.com/doc.pdf", expected_kind="pdf") is False


def test_probe_accepts_pdf_response_for_pdf(monkeypatch):
    response = DummyResponse(status_code=200, headers={"content-type": "application/pdf"})
    monkeypatch.setattr("app.services.probe.httpx.Client", lambda **kwargs: DummyClient(response))

    service = ProbeService()

    assert service._check_url("https://example.com/doc.pdf", expected_kind="pdf") is True


def test_fetch_rejects_invalid_pdf_payload():
    assert is_valid_artifact_payload("pdf", "text/html", b"<!doctype html>") is False
    assert is_valid_artifact_payload("pdf", "application/pdf", b"<!doctype html>") is False


def test_fetch_accepts_valid_pdf_payload():
    assert is_valid_artifact_payload("pdf", "application/pdf", b"%PDF-1.7\n") is True

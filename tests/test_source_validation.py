from app.services.fetch import FetchService
from app.services.probe import ProbeService


class DummyResponse:
    def __init__(self, status_code=200, headers=None, content=b""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content


class DummyClient:
    def __init__(self, head_response, get_response=None):
        self.head_response = head_response
        self.get_response = get_response or head_response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def head(self, url):
        return self.head_response

    def get(self, url, headers=None):
        return self.get_response


def test_probe_rejects_html_response_for_pdf(monkeypatch):
    head_response = DummyResponse(status_code=200, headers={"content-type": "text/html"})
    get_response = DummyResponse(
        status_code=200,
        headers={"content-type": "text/html"},
        content=b"<!doctype html>",
    )
    monkeypatch.setattr(
        "app.services.probe.httpx.Client",
        lambda **kwargs: DummyClient(head_response, get_response),
    )

    service = ProbeService()

    assert service._check_url("https://example.com/doc.pdf", expected_kind="pdf") is False


def test_probe_accepts_pdf_response_for_pdf(monkeypatch):
    response = DummyResponse(status_code=200, headers={"content-type": "application/pdf"})
    monkeypatch.setattr("app.services.probe.httpx.Client", lambda **kwargs: DummyClient(response))

    service = ProbeService()

    assert service._check_url("https://example.com/doc.pdf", expected_kind="pdf") is True


def test_probe_falls_back_to_get_for_html_and_rejects_shell(monkeypatch):
    head_response = DummyResponse(status_code=200, headers={"content-type": "text/html"})
    get_response = DummyResponse(
        status_code=200,
        headers={"content-type": "text/html"},
        content=b'''<!doctype html><html><body><div id="app"></div><script src="/assets/index-ABC.js"></script></body></html>''',
    )
    monkeypatch.setattr(
        "app.services.probe.httpx.Client",
        lambda **kwargs: DummyClient(head_response, get_response),
    )

    result = ProbeService()._check_url_detailed("https://example.com/doc", expected_kind="html")

    assert result.is_available is False
    assert result.reason_code == "source_invalid_html_shell"
    assert result.checked_via == "get"


def test_probe_falls_back_to_get_when_head_is_inconclusive(monkeypatch):
    head_response = DummyResponse(status_code=200, headers={})
    get_response = DummyResponse(
        status_code=200,
        headers={"content-type": "text/html"},
        content=b"<html><body><main><p>valid content" + (b"x" * 400) + b"</p></main></body></html>",
    )
    monkeypatch.setattr(
        "app.services.probe.httpx.Client",
        lambda **kwargs: DummyClient(head_response, get_response),
    )

    result = ProbeService()._check_url_detailed("https://example.com/doc", expected_kind="html")

    assert result.is_available is True
    assert result.reason_code is None
    assert result.checked_via == "get"


def test_fetch_rejects_invalid_pdf_payload():
    assert FetchService._is_valid_artifact_payload("pdf", "text/html", b"<!doctype html>") is False
    assert FetchService._is_valid_artifact_payload("pdf", "application/pdf", b"<!doctype html>") is False


def test_fetch_accepts_valid_pdf_payload():
    assert FetchService._is_valid_artifact_payload("pdf", "application/pdf", b"%PDF-1.7\n") is True


def test_fetch_rejects_html_shell_payload():
    shell = b'''<!doctype html><html><body><div id="app"></div><script src="/assets/index-ABC.js"></script></body></html>'''
    assert FetchService._is_valid_artifact_payload("html", "text/html", shell) is False


def test_fetch_accepts_valid_html_payload():
    html = b"<html><body><main><p>valid content" + (b"x" * 400) + b"</p></main></body></html>"
    assert FetchService._is_valid_artifact_payload("html", "text/html", html) is True

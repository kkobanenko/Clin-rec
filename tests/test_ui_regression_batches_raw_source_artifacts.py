from app.ui.app import build_preview_payload, describe_evidence_result


class TestUiRegressionBatchRawSourceArtifacts:
    def test_documents_raw_source_artifacts_actions(self):
        preview = build_preview_payload(
            {"ok": True, "content_type": "text/html", "content": b"<html>artifact</html>"}
        )
        evidence = describe_evidence_result(
            {"ok": True, "data": {"items": [{"id": 1, "relation_type": "signal"}], "total": 1}}
        )
        empty = describe_evidence_result(
            {"ok": True, "data": {"items": [], "total": 0}}
        )

        assert preview["kind"] == "text"
        assert evidence["state"] == "rows"
        assert empty["state"] == "empty"

    def test_preview_html_local_content(self):
        """HTML preview shows decoded artifact text, not external URL."""
        payload = build_preview_payload(
            {"ok": True, "content_type": "text/html", "content": b"<h1>Clinical Rec</h1>"}
        )
        assert payload["kind"] == "text"
        assert "Clinical Rec" in payload["message"]

    def test_preview_pdf_shows_fallback_not_iframe(self):
        """PDF preview does not attempt inline display; returns info message."""
        payload = build_preview_payload(
            {"ok": True, "content_type": "application/pdf", "content": b"%PDF-1.4"}
        )
        assert payload["kind"] == "info"
        assert "PDF" in payload["message"] or "preview" in payload["message"].lower()

    def test_preview_error_when_download_fails(self):
        """Preview shows error state when artifact fetch fails."""
        payload = build_preview_payload(
            {"ok": False, "detail": "Not Found", "content": None, "content_type": None}
        )
        assert payload["kind"] == "error"
        assert "Not Found" in payload["message"] or "failed" in payload["message"].lower()

    def test_evidence_error_state(self):
        """Evidence shows error state when API returns non-200."""
        result = describe_evidence_result(
            {"ok": False, "status_code": 500, "detail": "Internal Server Error", "data": None}
        )
        assert result["state"] == "error"
        assert "500" in result["message"] or "failed" in result["message"].lower()

    def test_evidence_empty_state(self):
        """Evidence shows empty state when API returns empty items."""
        result = describe_evidence_result(
            {"ok": True, "data": {"items": [], "total": 0}}
        )
        assert result["state"] == "empty"
        assert result["total"] == 0

    def test_download_unavailable_error_payload(self):
        """fetch_artifact_bytes returns structured error on HTTP failure."""
        from unittest.mock import patch, MagicMock
        import httpx
        from app.ui.app import fetch_artifact_bytes

        fake_response = MagicMock()
        fake_response.status_code = 404
        fake_response.text = "Not Found"
        fake_response.reason_phrase = "Not Found"
        fake_response.json.side_effect = ValueError

        artifact = {
            "id": 99,
            "artifact_type": "html",
            "content_type": "text/html",
            "download_url": "/documents/1/artifacts/99/download",
            "preview_url": "/documents/1/artifacts/99/download?disposition=inline",
        }

        with patch("httpx.get", side_effect=httpx.HTTPStatusError(
            "404", request=MagicMock(), response=fake_response
        )):
            result = fetch_artifact_bytes(artifact)

        assert result["ok"] is False
        assert result["content"] is None
        assert result["status_code"] == 404

    def test_fetch_artifact_bytes_no_url_returns_error(self):
        """fetch_artifact_bytes returns error when artifact has no download URL."""
        from app.ui.app import fetch_artifact_bytes

        artifact = {
            "id": 1,
            "artifact_type": "html",
            "content_type": "text/html",
            "download_url": None,
            "preview_url": None,
        }
        result = fetch_artifact_bytes(artifact)
        assert result["ok"] is False
        assert "unavailable" in (result.get("detail") or "").lower()


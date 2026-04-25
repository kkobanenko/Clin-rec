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

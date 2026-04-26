from app.ui.app import _artifact_filename, build_preview_payload


def test_build_preview_payload_formats_json() -> None:
    payload = build_preview_payload(
        {
            "ok": True,
            "content_type": "application/json",
            "content": b'{"title":"A","rules":["1","x"]}',
        }
    )
    assert payload["kind"] == "text"
    assert '"title": "A"' in payload["message"]


def test_artifact_filename_for_json_and_derived_types() -> None:
    assert _artifact_filename({"id": 1, "artifact_type": "json"}).endswith(".json")
    assert _artifact_filename({"id": 2, "artifact_type": "cleaned_html"}).endswith(".html")
    assert _artifact_filename({"id": 3, "artifact_type": "ocr_text"}).endswith(".txt")
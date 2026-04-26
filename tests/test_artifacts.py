from app.services.artifacts import (
    CLEANED_HTML,
    DERIVED_BLOCKS,
    OCR_TEXT,
    RAW_HTML,
    RAW_JSON,
    RAW_PDF,
    artifact_content_type,
    artifact_extension,
    is_derived_artifact,
    is_raw_artifact,
)


def test_artifact_extension_mapping() -> None:
    assert artifact_extension(RAW_JSON) == "json"
    assert artifact_extension(RAW_HTML) == "html"
    assert artifact_extension(RAW_PDF) == "pdf"
    assert artifact_extension(CLEANED_HTML) == "html"
    assert artifact_extension(OCR_TEXT) == "txt"
    assert artifact_extension(DERIVED_BLOCKS) == "json"
    assert artifact_extension("unknown") == "bin"


def test_artifact_content_type_mapping() -> None:
    assert artifact_content_type(RAW_JSON) == "application/json"
    assert artifact_content_type(RAW_HTML) == "text/html"
    assert artifact_content_type(RAW_PDF) == "application/pdf"
    assert artifact_content_type(CLEANED_HTML) == "text/html"
    assert artifact_content_type(OCR_TEXT) == "text/plain"
    assert artifact_content_type(DERIVED_BLOCKS) == "application/json"
    assert artifact_content_type("unknown") == "application/octet-stream"


def test_artifact_type_classification() -> None:
    assert is_raw_artifact(RAW_JSON)
    assert is_raw_artifact(RAW_HTML)
    assert is_raw_artifact(RAW_PDF)
    assert not is_raw_artifact(CLEANED_HTML)

    assert is_derived_artifact(CLEANED_HTML)
    assert is_derived_artifact(OCR_TEXT)
    assert is_derived_artifact(DERIVED_BLOCKS)
    assert not is_derived_artifact(RAW_JSON)
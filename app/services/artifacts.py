"""Artifact type abstraction helpers for JSON-first pipeline."""

RAW_JSON = "json"
RAW_HTML = "html"
RAW_PDF = "pdf"
CLEANED_HTML = "cleaned_html"
OCR_TEXT = "ocr_text"
DERIVED_BLOCKS = "derived_blocks"


def artifact_extension(artifact_type: str) -> str:
    mapping = {
        RAW_JSON: "json",
        RAW_HTML: "html",
        RAW_PDF: "pdf",
        CLEANED_HTML: "html",
        OCR_TEXT: "txt",
        DERIVED_BLOCKS: "json",
    }
    return mapping.get(artifact_type, "bin")


def artifact_content_type(artifact_type: str) -> str:
    mapping = {
        RAW_JSON: "application/json",
        RAW_HTML: "text/html",
        RAW_PDF: "application/pdf",
        CLEANED_HTML: "text/html",
        OCR_TEXT: "text/plain",
        DERIVED_BLOCKS: "application/json",
    }
    return mapping.get(artifact_type, "application/octet-stream")


def is_raw_artifact(artifact_type: str) -> bool:
    return artifact_type in {RAW_JSON, RAW_HTML, RAW_PDF}


def is_derived_artifact(artifact_type: str) -> bool:
    return artifact_type in {CLEANED_HTML, OCR_TEXT, DERIVED_BLOCKS}
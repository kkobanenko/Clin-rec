"""OCR-first placeholder contract for image blocks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float | None
    coordinates: dict | None
    engine: str


def run_ocr(image_bytes: bytes | None) -> OcrResult:
    if not image_bytes:
        return OcrResult(text="", confidence=None, coordinates=None, engine="disabled")
    # Placeholder contract: engine integration is added later without breaking callers.
    return OcrResult(text="", confidence=None, coordinates=None, engine="not_configured")
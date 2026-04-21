"""
Проверка байтов сырья (html/pdf) после загрузки и при отдаче через API.

Единые правила для FetchService и GET /documents, чтобы не показывать
SPA-заглушки и «pdf» с HTML-телом.
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True, slots=True)
class ArtifactValidationResult:
    is_valid: bool
    reason_code: str | None = None


def looks_like_spa_shell(data: bytes) -> bool:
    """
    Эвристика: ответ похож на каркас Vue/SPA рубрикатора (пустой #app + bundle), без текста КР.

    После Playwright в DOM часто остаются #app и /assets/index-*.js; объём HTML уже большой.
    Голая оболочка обычно <2 КБ (~610 байт). Большие ответы не считаем shell по этой эвристике.
    """
    if len(data) >= 3000:
        return False
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        return False
    if not text:
        return False
    low = text.lower()
    has_app_root = 'id="app"' in low or "id='app'" in low
    has_asset_bundle = "/assets/index-" in low and "<script" in low
    soup = BeautifulSoup(text, "lxml")
    body_text = soup.get_text(" ", strip=True)
    body_text_short = len(body_text) < 200
    return has_app_root and has_asset_bundle and body_text_short


def is_valid_pdf_payload(content_type: str | None, data: bytes) -> bool:
    """PDF: заголовок application/pdf и сигнатура %PDF-."""
    return validate_artifact_payload("pdf", content_type, data).is_valid


def validate_artifact_payload(
    artifact_type: str,
    content_type: str | None,
    data: bytes,
) -> ArtifactValidationResult:
    """Возвращает результат проверки и код причины отказа."""
    normalized_ct = (content_type or "").lower()
    if artifact_type == "pdf":
        if "application/pdf" not in normalized_ct:
            return ArtifactValidationResult(False, "source_invalid_pdf_content_type")
        if not data.startswith(b"%PDF-"):
            return ArtifactValidationResult(False, "source_invalid_pdf_signature")
        return ArtifactValidationResult(True)

    if artifact_type == "html":
        if not ("text/html" in normalized_ct or "application/xhtml+xml" in normalized_ct):
            return ArtifactValidationResult(False, "source_invalid_html_content_type")
        if looks_like_spa_shell(data):
            return ArtifactValidationResult(False, "source_invalid_html_shell")
        return ArtifactValidationResult(True)

    return ArtifactValidationResult(True)


def is_valid_html_payload(content_type: str | None, data: bytes) -> bool:
    """HTML: ожидаемый content-type и не SPA-shell."""
    return validate_artifact_payload("html", content_type, data).is_valid


def is_valid_artifact_payload(artifact_type: str, content_type: str | None, data: bytes) -> bool:
    """
    Проверка соответствия байтов заявленному типу артефакта.
    Используется при fetch и при отдаче/фильтрации в API.
    """
    return validate_artifact_payload(artifact_type, content_type, data).is_valid

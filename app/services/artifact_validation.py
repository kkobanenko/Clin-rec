"""
Проверка байтов сырья (html/pdf) после загрузки и при отдаче через API.

Единые правила для FetchService и GET /documents, чтобы не показывать
SPA-заглушки и «pdf» с HTML-телом.
"""

from __future__ import annotations

from bs4 import BeautifulSoup


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
    normalized_ct = (content_type or "").lower()
    if "application/pdf" not in normalized_ct:
        return False
    return data.startswith(b"%PDF-")


def is_valid_html_payload(content_type: str | None, data: bytes) -> bool:
    """HTML: ожидаемый content-type и не SPA-shell."""
    normalized_ct = (content_type or "").lower()
    if not ("text/html" in normalized_ct or "application/xhtml+xml" in normalized_ct):
        return False
    return not looks_like_spa_shell(data)


def is_valid_artifact_payload(artifact_type: str, content_type: str | None, data: bytes) -> bool:
    """
    Проверка соответствия байтов заявленному типу артефакта.
    Используется при fetch и при отдаче/фильтрации в API.
    """
    if artifact_type == "pdf":
        return is_valid_pdf_payload(content_type, data)
    if artifact_type == "html":
        return is_valid_html_payload(content_type, data)
    return True

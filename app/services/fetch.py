"""Fetch service — downloads raw HTML/JSON/PDF artifacts and stores them in S3."""

import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.storage import artifact_key, content_hash, upload_artifact
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


class FetchService:
    def fetch(self, version_id: int) -> None:
        session = get_sync_session()
        try:
            version = session.get(DocumentVersion, version_id)
            if not version:
                logger.error("DocumentVersion %d not found", version_id)
                return

            doc = session.get(DocumentRegistry, version.registry_id)
            if not doc:
                logger.error("DocumentRegistry %d not found", version.registry_id)
                return

            fetched_any = False

            # Fetch HTML
            if doc.html_url:
                if self._fetch_artifact(session, doc, version, doc.html_url, "html", "text/html"):
                    fetched_any = True

            # Fetch PDF
            if doc.pdf_url:
                if self._fetch_artifact(session, doc, version, doc.pdf_url, "pdf", "application/pdf"):
                    fetched_any = True

            session.commit()

            if fetched_any:
                # Update version hash from artifacts
                artifacts = (
                    session.query(SourceArtifact)
                    .filter_by(document_version_id=version_id)
                    .all()
                )
                combined_hash = content_hash(
                    "".join(sorted(a.content_hash for a in artifacts)).encode()
                )
                version.version_hash = combined_hash
                session.commit()

                # Queue normalization
                from app.workers.tasks.normalize import normalize_document

                normalize_document.delay(version_id)
                logger.info("Fetched artifacts for version %d (doc %d)", version_id, doc.id)
            else:
                logger.warning("No artifacts fetched for version %d", version_id)

        finally:
            session.close()

    def _fetch_artifact(
        self,
        session,
        doc: DocumentRegistry,
        version: DocumentVersion,
        url: str,
        artifact_type: str,
        expected_content_type: str,
    ) -> bool:
        """Download a single artifact. Returns True on success."""
        for attempt in range(MAX_RETRIES):
            try:
                data, actual_ct = self._download_payload(url, artifact_type, expected_content_type)
                data_hash = content_hash(data)

                if not self._is_valid_artifact_payload(artifact_type, actual_ct, data):
                    logger.warning(
                        "Skipping %s artifact for version %d: unexpected content-type=%s",
                        artifact_type,
                        version.id,
                        actual_ct,
                    )
                    return False

                # Check if we already have this exact artifact
                existing = (
                    session.query(SourceArtifact)
                    .filter_by(
                        document_version_id=version.id,
                        artifact_type=artifact_type,
                        content_hash=data_hash,
                    )
                    .first()
                )
                if existing:
                    logger.debug("Artifact already exists: %s for version %d", artifact_type, version.id)
                    return True

                ext = "html" if artifact_type == "html" else artifact_type
                key = artifact_key(doc.id, version.id, artifact_type, ext)
                upload_artifact(data, key, actual_ct)

                artifact = SourceArtifact(
                    document_version_id=version.id,
                    artifact_type=artifact_type,
                    raw_path=key,
                    content_hash=data_hash,
                    content_type=actual_ct,
                    # В режиме Playwright оригинальные заголовки HTTP недоступны.
                    headers_json={"source_url": url, "fetch_mode": self._detect_fetch_mode(artifact_type, actual_ct)},
                    fetched_at=datetime.now(timezone.utc),
                )
                session.add(artifact)
                session.flush()
                return True

            except httpx.HTTPStatusError as e:
                logger.warning("HTTP error fetching %s (attempt %d): %s", url, attempt + 1, e)
            except Exception as e:
                logger.warning("Error fetching %s (attempt %d): %s", url, attempt + 1, e)

            if attempt < MAX_RETRIES - 1:
                import time
                time.sleep(RETRY_BACKOFF * (attempt + 1))

        return False

    @staticmethod
    def _is_valid_artifact_payload(artifact_type: str, content_type: str | None, data: bytes) -> bool:
        normalized_ct = (content_type or "").lower()
        if artifact_type == "pdf":
            return "application/pdf" in normalized_ct and data.startswith(b"%PDF-")
        if artifact_type == "html":
            if not ("text/html" in normalized_ct or "application/xhtml+xml" in normalized_ct):
                return False
            return not FetchService._looks_like_spa_shell(data)
        return True

    def _download_payload(
        self,
        url: str,
        artifact_type: str,
        expected_content_type: str,
    ) -> tuple[bytes, str]:
        """Скачивает payload через HTTP; для SPA HTML делает fallback на Playwright."""
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        data = resp.content
        actual_ct = resp.headers.get("content-type", expected_content_type)

        # Для HTML-страниц рубрикатора часто прилетает SPA-оболочка. В этом случае
        # пробуем рендер через Playwright и сохраняем уже готовый HTML DOM.
        if artifact_type == "html" and self._looks_like_spa_shell(data):
            rendered_html = self._render_html_with_playwright(url)
            if rendered_html:
                return rendered_html, "text/html; charset=utf-8"

        return data, actual_ct

    @staticmethod
    def _detect_fetch_mode(artifact_type: str, content_type: str | None) -> str:
        normalized_ct = (content_type or "").lower()
        if artifact_type == "pdf":
            return "http_pdf"
        if "text/html" in normalized_ct or "application/xhtml+xml" in normalized_ct:
            return "http_or_playwright_html"
        return "http_raw"

    @staticmethod
    def _looks_like_spa_shell(data: bytes) -> bool:
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            return False
        if not text:
            return False
        low = text.lower()
        # Типичный shell рубрикатора: пустой div#app + bundle assets/index-*.js
        has_app_root = 'id="app"' in low or "id='app'" in low
        has_asset_bundle = "/assets/index-" in low and "<script" in low
        soup = BeautifulSoup(text, "lxml")
        body_text = soup.get_text(" ", strip=True)
        body_text_short = len(body_text) < 200
        return has_app_root and has_asset_bundle and body_text_short

    @staticmethod
    def _render_html_with_playwright(url: str) -> bytes | None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            logger.warning("playwright not installed — SPA html fallback unavailable")
            return None

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    context = browser.new_context()
                    page = context.new_page()
                    page.goto(url, wait_until="networkidle", timeout=120000)
                    page.wait_for_timeout(2500)
                    # Сохраняем полностью отрендеренный DOM в HTML-артефакт.
                    html = page.content()
                finally:
                    browser.close()
        except Exception as e:
            logger.warning("Playwright render failed for %s: %s", url, e)
            return None

        if not html or len(html) < 500:
            return None
        return html.encode("utf-8")

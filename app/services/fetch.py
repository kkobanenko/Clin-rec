"""Fetch service — downloads raw HTML/JSON/PDF artifacts and stores them in S3."""

import logging
import re
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.storage import artifact_key, content_hash, upload_artifact
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.services.artifact_validation import is_valid_artifact_payload, looks_like_spa_shell

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


def _rubricator_page_url(path_segment: str, external_id: str) -> str:
    """Полный URL страницы на cr.minzdrav.gov.ru (view-cr, preview-cr, …)."""
    base = settings.rubricator_base_url.rstrip("/")
    seg = path_segment.strip("/")
    return f"{base}/{seg}/{external_id.strip()}"


def _http_headers(*, for_pdf: bool) -> dict[str, str]:
    """Браузероподобные заголовки; User-Agent как у discovery API."""
    ua = settings.rubricator_api_user_agent
    if for_pdf:
        accept = "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8"
    else:
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    return {
        "User-Agent": ua,
        "Accept": accept,
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
    }


class FetchService:
    def fetch(
        self,
        version_id: int,
        *,
        force: bool = False,
        celery_task_id: str | None = None,
    ) -> dict:
        from app.services.pipeline_event_log import write_pipeline_event

        session = get_sync_session()
        try:
            version = session.get(DocumentVersion, version_id)
            if not version:
                logger.error("DocumentVersion %d not found", version_id)
                return {"ok": False, "error": "document_version_not_found", "version_id": version_id}

            doc = session.get(DocumentRegistry, version.registry_id)
            if not doc:
                logger.error("DocumentRegistry %d not found", version.registry_id)
                return {
                    "ok": False,
                    "error": "document_registry_not_found",
                    "version_id": version_id,
                    "registry_id": version.registry_id,
                }

            write_pipeline_event(
                document_registry_id=doc.id,
                document_version_id=version_id,
                celery_task_id=celery_task_id,
                stage="fetch",
                status="started",
                message="fetch started",
                detail_json={"force": force},
            )

            if force:
                deleted = (
                    session.query(SourceArtifact)
                    .filter_by(document_version_id=version_id)
                    .delete(synchronize_session=False)
                )
                session.flush()
                logger.info("fetch force: removed %d artifact row(s) for version %d", deleted, version_id)

            html_ok = False
            pdf_ok = False

            # HTML: сначала view-cr/{external_id} (основной контент), затем html_url из реестра (fallback).
            ext = (doc.external_id or "").strip()
            if ext:
                view_cr_url = _rubricator_page_url(settings.rubricator_view_cr_path, ext)
                logger.info("fetch html: primary view-cr %s", view_cr_url)
                html_ok = self._fetch_artifact(
                    session, doc, version, view_cr_url, "html", "text/html", force=force
                )
            if not html_ok and doc.html_url:
                logger.info("fetch html: fallback registry html_url %s", doc.html_url)
                html_ok = self._fetch_artifact(
                    session, doc, version, doc.html_url, "html", "text/html", force=force
                )

            # PDF: URL из реестра часто отдаёт SPA; затем загрузка с preview-cr через Playwright.
            if doc.pdf_url:
                pdf_ok = self._fetch_artifact(
                    session, doc, version, doc.pdf_url, "pdf", "application/pdf", force=force
                )
            if not pdf_ok and ext:
                pdf_ok = self._fetch_pdf_via_playwright_preview(session, doc, version, force=force)

            fetched_any = html_ok or pdf_ok

            session.commit()

            normalize_task_id: str | None = None

            if fetched_any:
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

                from app.workers.tasks.normalize import normalize_document

                async_res = normalize_document.delay(version_id)
                normalize_task_id = async_res.id
                logger.info("Fetched artifacts for version %d (doc %d)", version_id, doc.id)
                write_pipeline_event(
                    document_registry_id=doc.id,
                    document_version_id=version_id,
                    celery_task_id=celery_task_id,
                    stage="fetch",
                    status="success",
                    message="fetch stored artifacts and queued normalize",
                    detail_json={
                        "force": force,
                        "html_ok": html_ok,
                        "pdf_ok": pdf_ok,
                        "normalize_task_id": normalize_task_id,
                    },
                )
            else:
                logger.warning("No artifacts fetched for version %d", version_id)
                write_pipeline_event(
                    document_registry_id=doc.id,
                    document_version_id=version_id,
                    celery_task_id=celery_task_id,
                    stage="fetch",
                    status="failure",
                    message="no valid html/pdf stored (validation or network)",
                    detail_json={
                        "force": force,
                        "html_ok": html_ok,
                        "pdf_ok": pdf_ok,
                        "html_url": doc.html_url,
                        "pdf_url": doc.pdf_url,
                        "hint": (
                            "pdf_url часто отдаёт text/html (SPA), а не PDF — успех зависит от html+Playwright."
                        ),
                    },
                )

            return {
                "ok": True,
                "version_id": version_id,
                "registry_id": doc.id,
                "force": force,
                "html_ok": html_ok,
                "pdf_ok": pdf_ok,
                "fetched_any": fetched_any,
                "normalize_task_id": normalize_task_id,
            }

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
        *,
        force: bool,
    ) -> bool:
        for attempt in range(MAX_RETRIES):
            try:
                data, actual_ct = self._download_payload(url, artifact_type, expected_content_type)

                if artifact_type == "pdf" and self._pdf_bytes_look_like_html(data, actual_ct):
                    logger.warning(
                        "pdf URL returned HTML (not binary PDF), skip: %s len=%d ct=%s",
                        url,
                        len(data),
                        actual_ct,
                    )
                    return False

                if not is_valid_artifact_payload(artifact_type, actual_ct, data):
                    logger.warning(
                        "Skipping %s artifact for version %d: ct=%s len=%d",
                        artifact_type,
                        version.id,
                        actual_ct,
                        len(data),
                    )
                    return False

                fetch_mode = self._detect_fetch_mode(artifact_type, actual_ct)
                return self._persist_source_artifact(
                    session,
                    doc,
                    version,
                    data,
                    artifact_type,
                    actual_ct,
                    url,
                    fetch_mode,
                    force=force,
                )

            except httpx.HTTPStatusError as e:
                logger.warning("HTTP error fetching %s (attempt %d): %s", url, attempt + 1, e)
            except Exception as e:
                logger.warning("Error fetching %s (attempt %d): %s", url, attempt + 1, e)

            if attempt < MAX_RETRIES - 1:
                import time

                time.sleep(RETRY_BACKOFF * (attempt + 1))

        return False

    def _persist_source_artifact(
        self,
        session,
        doc: DocumentRegistry,
        version: DocumentVersion,
        data: bytes,
        artifact_type: str,
        actual_ct: str,
        source_url: str,
        fetch_mode: str,
        *,
        force: bool,
    ) -> bool:
        """
        Сохраняет уже проверенные байты в S3 и строку SourceArtifact.
        Вызывается из HTTP-fetch и из Playwright (preview-cr PDF).
        """
        data_hash = content_hash(data)
        if not force:
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
            headers_json={"source_url": source_url, "fetch_mode": fetch_mode},
            fetched_at=datetime.now(timezone.utc),
        )
        session.add(artifact)
        session.flush()
        return True

    def _pdf_bytes_look_like_html(self, data: bytes, actual_ct: str | None) -> bool:
        """Реестровый pdf_url часто отдаёт HTML-оболочку вместо бинарного PDF."""
        if "text/html" in (actual_ct or "").lower():
            return True
        head = data[:64].strip().lower()
        return head.startswith(b"<!doctype") or head.startswith(b"<html")

    def _fetch_pdf_via_playwright_preview(
        self,
        session,
        doc: DocumentRegistry,
        version: DocumentVersion,
        *,
        force: bool,
    ) -> bool:
        """
        Страница preview-cr: кнопка «Скачать … PDF» отдаёт настоящий файл через браузерный download.
        HTTP pdf_url с сайта часто — SPA (~610 B), поэтому добираем PDF так.
        """
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            logger.warning("playwright not installed — preview-cr PDF недоступен")
            return False

        ext = (doc.external_id or "").strip()
        if not ext:
            return False

        preview_url = _rubricator_page_url(settings.rubricator_preview_cr_path, ext)
        ua = settings.rubricator_api_user_agent

        for attempt in range(MAX_RETRIES):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                    try:
                        context = browser.new_context(
                            user_agent=ua,
                            locale="ru-RU",
                            extra_http_headers={
                                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                            },
                        )
                        page = context.new_page()
                        page.goto(preview_url, wait_until="networkidle", timeout=120000)
                        page.wait_for_timeout(4000)

                        # Ищем элемент, который запускает скачивание PDF (подписи на сайте могут слегка отличаться).
                        download_trigger = None
                        name_pdf = re.compile(r"скачать.{0,60}pdf", re.IGNORECASE)
                        for role in ("button", "link"):
                            loc = page.get_by_role(role, name=name_pdf)
                            if loc.count() > 0:
                                download_trigger = loc.first
                                break

                        if download_trigger is None:
                            loc = page.get_by_text(re.compile(r"скачать[^\n]{0,40}pdf", re.IGNORECASE))
                            if loc.count() > 0:
                                download_trigger = loc.first

                        if download_trigger is None:
                            for role in ("button", "link"):
                                loc = page.get_by_role(role, name=re.compile(r"pdf", re.IGNORECASE))
                                if loc.count() > 0:
                                    download_trigger = loc.first
                                    break

                        if download_trigger is None:
                            logger.warning("preview-cr: не найдена кнопка/ссылка PDF для %s", preview_url)
                            return False

                        with page.expect_download(timeout=120000) as download_info:
                            download_trigger.click()
                        download = download_info.value
                        path = download.path()
                        if not path:
                            logger.warning("preview-cr: пустой path у download для %s", preview_url)
                            return False
                        with open(path, "rb") as f:
                            data = f.read()
                    finally:
                        browser.close()

                actual_ct = "application/pdf"
                if not is_valid_artifact_payload("pdf", actual_ct, data):
                    logger.warning(
                        "preview-cr: байты не прошли валидацию PDF (len=%d) %s",
                        len(data),
                        preview_url,
                    )
                    return False

                return self._persist_source_artifact(
                    session,
                    doc,
                    version,
                    data,
                    "pdf",
                    actual_ct,
                    preview_url,
                    "playwright_preview_pdf",
                    force=force,
                )

            except Exception as e:
                logger.warning("preview-cr PDF attempt %d failed for %s: %s", attempt + 1, preview_url, e)

            if attempt < MAX_RETRIES - 1:
                import time

                time.sleep(RETRY_BACKOFF * (attempt + 1))

        return False

    def _download_payload(
        self,
        url: str,
        artifact_type: str,
        expected_content_type: str,
    ) -> tuple[bytes, str]:
        headers = _http_headers(for_pdf=(artifact_type == "pdf"))
        with httpx.Client(timeout=90.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            resp.raise_for_status()
        data = resp.content
        actual_ct = resp.headers.get("content-type", expected_content_type)
        logger.info(
            "fetch GET %s type=%s len=%d content-type=%s",
            url,
            artifact_type,
            len(data),
            actual_ct,
        )

        if artifact_type == "html" and looks_like_spa_shell(data):
            logger.info("SPA shell for html, Playwright: %s", url)
            rendered_html = self._render_html_with_playwright(url)
            if rendered_html:
                return rendered_html, "text/html; charset=utf-8"
            logger.warning("Playwright did not yield valid HTML for %s", url)

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
    def _render_html_with_playwright(url: str) -> bytes | None:
        try:
            from playwright.sync_api import sync_playwright
        except Exception:
            logger.warning("playwright not installed — SPA html fallback unavailable")
            return None

        ua = settings.rubricator_api_user_agent
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    context = browser.new_context(
                        user_agent=ua,
                        locale="ru-RU",
                        extra_http_headers={
                            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                        },
                    )
                    page = context.new_page()
                    page.goto(url, wait_until="networkidle", timeout=120000)
                    try:
                        page.wait_for_function(
                            """() => {
                              const t = document.body && document.body.innerText
                                ? document.body.innerText.trim()
                                : '';
                              return t.length > 400;
                            }""",
                            timeout=90000,
                        )
                    except Exception as wait_err:
                        logger.warning("Playwright wait_for_function: %s", wait_err)
                    page.wait_for_timeout(3000)
                    html = page.content()
                    if html:
                        logger.info("Playwright content len=%d", len(html))
                finally:
                    browser.close()
        except Exception as e:
            logger.warning("Playwright render failed for %s: %s", url, e)
            return None

        if not html or len(html) < 500:
            logger.warning("Playwright HTML too short (%s bytes) for %s", len(html or ""), url)
            return None
        raw = html.encode("utf-8")
        if looks_like_spa_shell(raw):
            logger.warning("Playwright output still looks like SPA shell for %s", url)
            return None
        return raw

"""Probe service — determines source availability (html/pdf) for each document."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion
from app.services.artifact_validation import validate_artifact_payload

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ProbeCheckResult:
    is_available: bool
    reason_code: str | None = None
    checked_via: str = "head"
    content_type: str | None = None


@dataclass(frozen=True, slots=True)
class ProbeServiceResult:
    document_registry_id: int | None
    document_version_id: int | None
    status: str
    source_primary: str | None = None
    reason_code: str | None = None
    html_reason_code: str | None = None
    pdf_reason_code: str | None = None
    queued_fetch: bool = False


class ProbeService:
    def probe(self, registry_id: int) -> ProbeServiceResult:
        session = get_sync_session()
        try:
            doc = session.get(DocumentRegistry, registry_id)
            if not doc:
                logger.error("Document registry %d not found", registry_id)
                return ProbeServiceResult(registry_id, None, "failed", reason_code="document_registry_not_found")

            html_result = self._check_url_detailed(doc.html_url, expected_kind="html") if doc.html_url else ProbeCheckResult(False, "source_missing_url", "none")
            pdf_result = self._check_url_detailed(doc.pdf_url, expected_kind="pdf") if doc.pdf_url else ProbeCheckResult(False, "source_missing_url", "none")
            html_available = html_result.is_available
            pdf_available = pdf_result.is_available

            # Also try to derive URLs from card_url if not set
            if not doc.html_url and doc.card_url:
                candidate_html = doc.card_url
                candidate_html_result = self._check_url_detailed(candidate_html, expected_kind="html")
                if candidate_html_result.is_available:
                    doc.html_url = candidate_html
                    html_available = True
                    html_result = candidate_html_result

            if not doc.pdf_url and doc.external_id:
                candidate_pdf = (
                    f"{settings.rubricator_base_url.rstrip('/')}/"
                    f"{settings.rubricator_pdf_path.strip('/')}/{doc.external_id}"
                )
                candidate_pdf_result = self._check_url_detailed(candidate_pdf, expected_kind="pdf")
                if candidate_pdf_result.is_available:
                    doc.pdf_url = candidate_pdf
                    pdf_available = True
                    pdf_result = candidate_pdf_result

            # Classify source type
            if html_available and pdf_available:
                source_primary = "html+pdf"
                available = "html,pdf"
            elif html_available:
                source_primary = "html"
                available = "html"
            elif pdf_available:
                source_primary = "pdf"
                available = "pdf"
            else:
                source_primary = "unknown"
                available = ""

            # Check for existing current version
            existing = (
                session.query(DocumentVersion)
                .filter_by(registry_id=registry_id, is_current=True)
                .first()
            )

            if existing:
                # Update existing version's source info
                existing.source_type_primary = source_primary
                existing.source_type_available = available
                version_id = existing.id
            else:
                version = DocumentVersion(
                    registry_id=registry_id,
                    source_type_primary=source_primary,
                    source_type_available=available,
                    detected_at=datetime.now(timezone.utc),
                    is_current=True,
                )
                session.add(version)
                session.flush()
                version_id = version.id

            session.commit()
            logger.info(
                "Probed document %d: source=%s html_reason=%s pdf_reason=%s",
                registry_id,
                source_primary,
                html_result.reason_code,
                pdf_result.reason_code,
            )

            # Queue fetch
            queued_fetch = False
            if source_primary != "unknown":
                from app.workers.tasks.fetch import fetch_document

                fetch_document.delay(version_id)
                queued_fetch = True

            return ProbeServiceResult(
                document_registry_id=registry_id,
                document_version_id=version_id,
                status="success" if source_primary != "unknown" else "degraded",
                source_primary=source_primary,
                reason_code=None if source_primary != "unknown" else "source_probe_inconclusive",
                html_reason_code=html_result.reason_code,
                pdf_reason_code=pdf_result.reason_code,
                queued_fetch=queued_fetch,
            )

        finally:
            session.close()

    def _check_url(self, url: str, expected_kind: str = "html") -> bool:
        return self._check_url_detailed(url, expected_kind=expected_kind).is_available

    def _check_url_detailed(self, url: str, expected_kind: str = "html") -> ProbeCheckResult:
        """Check if a URL is accessible and matches the expected content kind."""
        if not url:
            return ProbeCheckResult(False, "source_missing_url", "none")
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                resp = client.head(url)
                if resp.status_code != 200:
                    return self._validate_with_get(client, url, expected_kind, "source_probe_inconclusive")
                content_type = (resp.headers.get("content-type") or "").lower()
                if expected_kind == "pdf" and "application/pdf" in content_type:
                    return ProbeCheckResult(True, None, "head", content_type)
                return self._validate_with_get(client, url, expected_kind, "source_probe_inconclusive")
        except Exception as e:
            logger.debug("URL check failed for %s: %s", url, e)
            return ProbeCheckResult(False, "source_probe_inconclusive", "head")

    def _validate_with_get(
        self,
        client: httpx.Client,
        url: str,
        expected_kind: str,
        fallback_reason: str,
    ) -> ProbeCheckResult:
        try:
            resp = client.get(url, headers={"Range": "bytes=0-4095"})
            if resp.status_code != 200 and resp.status_code != 206:
                return ProbeCheckResult(False, fallback_reason, "get")
            content_type = resp.headers.get("content-type")
            validation = validate_artifact_payload(expected_kind, content_type, resp.content)
            return ProbeCheckResult(validation.is_valid, validation.reason_code, "get", content_type)
        except Exception as e:
            logger.debug("GET fallback failed for %s: %s", url, e)
            return ProbeCheckResult(False, fallback_reason, "get")

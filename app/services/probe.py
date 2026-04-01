"""Probe service — determines source availability (html/pdf) for each document."""

import logging
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion
from app.workers.tasks.fetch import fetch_document

logger = logging.getLogger(__name__)


class ProbeService:
    def probe(self, registry_id: int) -> None:
        session = get_sync_session()
        try:
            doc = session.get(DocumentRegistry, registry_id)
            if not doc:
                logger.error("Document registry %d not found", registry_id)
                return

            html_available = self._check_url(doc.html_url) if doc.html_url else False
            pdf_available = self._check_url(doc.pdf_url) if doc.pdf_url else False

            # Also try to derive URLs from card_url if not set
            if not doc.html_url and doc.card_url:
                candidate_html = doc.card_url
                if self._check_url(candidate_html):
                    doc.html_url = candidate_html
                    html_available = True

            if not doc.pdf_url and doc.external_id:
                candidate_pdf = (
                    f"{settings.rubricator_base_url.rstrip('/')}/"
                    f"{settings.rubricator_pdf_path.strip('/')}/{doc.external_id}"
                )
                if self._check_url(candidate_pdf):
                    doc.pdf_url = candidate_pdf
                    pdf_available = True

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
            logger.info("Probed document %d: source=%s", registry_id, source_primary)

            # Queue fetch
            if source_primary != "unknown":
                fetch_document.delay(version_id)

        finally:
            session.close()

    def _check_url(self, url: str) -> bool:
        """Check if a URL is accessible (HEAD request)."""
        if not url:
            return False
        try:
            with httpx.Client(timeout=15, follow_redirects=True) as client:
                resp = client.head(url)
                return resp.status_code == 200
        except Exception as e:
            logger.debug("URL check failed for %s: %s", url, e)
            return False

"""Fetch service — downloads raw HTML/JSON/PDF artifacts and stores them in S3."""

import logging
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.storage import artifact_key, content_hash, upload_artifact
from app.core.sync_database import get_sync_session
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.workers.tasks.normalize import normalize_document

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
                with httpx.Client(timeout=60, follow_redirects=True) as client:
                    resp = client.get(url)
                    resp.raise_for_status()

                data = resp.content
                data_hash = content_hash(data)

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
                actual_ct = resp.headers.get("content-type", expected_content_type)
                upload_artifact(data, key, actual_ct)

                artifact = SourceArtifact(
                    document_version_id=version.id,
                    artifact_type=artifact_type,
                    raw_path=key,
                    content_hash=data_hash,
                    content_type=actual_ct,
                    headers_json=dict(resp.headers),
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

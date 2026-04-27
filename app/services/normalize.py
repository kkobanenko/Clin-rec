"""Normalize service — cleans raw HTML/PDF, splits into sections and fragments."""

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from app.core.storage import content_hash, download_artifact, upload_artifact
from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion, SourceArtifact
from app.models.evidence import PairEvidence
from app.models.text import DocumentSection, TextFragment
from app.services.cleaned_html import sanitize_html
from app.services.json_blocks import collect_canonical_blocks, serialize_rules_to_text

logger = logging.getLogger(__name__)

NORMALIZER_VERSION = "1.0.0"

# Elements to remove from HTML before processing
NOISE_SELECTORS = [
    "nav", "header", "footer", ".cookie-banner", ".breadcrumb",
    ".navigation", ".sidebar", ".toolbar", "script", "style",
    "noscript", "iframe", ".modal", ".popup",
]


@dataclass(frozen=True, slots=True)
class NormalizeExtractionResult:
    sections: list["NormalizedSectionCandidate"]
    source_used: str | None = None
    reason_code: str | None = None
    source_artifact_id: int | None = None
    source_artifact_type: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedFragmentCandidate:
    fragment_type: str
    fragment_text: str
    source_block_id: str | None = None
    source_path: str | None = None
    content_kind: str | None = None
    raw_html: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedSectionCandidate:
    section_title: str
    section_path: str
    fragments: list[NormalizedFragmentCandidate]
    source_block_id: str | None = None
    source_path: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizeServiceResult:
    document_registry_id: int | None
    document_version_id: int
    status: str
    sections_count: int = 0
    fragments_count: int = 0
    source_used: str | None = None
    reason_code: str | None = None
    queued_extract: bool = False


class NormalizeService:
    def normalize(self, version_id: int) -> NormalizeServiceResult:
        session = get_sync_session()
        try:
            version = session.get(DocumentVersion, version_id)
            if not version:
                logger.error("DocumentVersion %d not found", version_id)
                return NormalizeServiceResult(None, version_id, "failed", reason_code="document_version_not_found")

            # Remove old sections/fragments for this version
            old_sections = session.query(DocumentSection).filter_by(document_version_id=version_id).all()
            for sec in old_sections:
                # Must delete pair_evidence before text_fragment due to FK constraint
                frag_ids = [f.id for f in session.query(TextFragment.id).filter_by(section_id=sec.id).all()]
                if frag_ids:
                    session.query(PairEvidence).filter(PairEvidence.fragment_id.in_(frag_ids)).delete(synchronize_session=False)
                session.query(TextFragment).filter_by(section_id=sec.id).delete()
                session.delete(sec)
            session.flush()

            # Get primary artifact
            artifacts = (
                session.query(SourceArtifact)
                .filter_by(document_version_id=version_id)
                .all()
            )

            json_artifact = next((a for a in artifacts if a.artifact_type == "json"), None)
            html_artifact = next((a for a in artifacts if a.artifact_type == "html"), None)
            pdf_artifact = next((a for a in artifacts if a.artifact_type == "pdf"), None)

            extraction = self._extract_sections_detailed(version, json_artifact, html_artifact, pdf_artifact)
            sections = extraction.sections

            if not sections:
                logger.warning("No sections extracted for version %d", version_id)
                return NormalizeServiceResult(
                    version.registry_id,
                    version_id,
                    "degraded",
                    source_used=extraction.source_used,
                    reason_code=extraction.reason_code,
                )

            # Write to DB
            version.normalizer_version = NORMALIZER_VERSION
            fragments_count = 0
            html_chunks: list[str] = []
            for sec_order, section in enumerate(sections):
                db_section = DocumentSection(
                    document_version_id=version_id,
                    section_path=section.section_path,
                    section_title=section.section_title,
                    section_order=sec_order,
                    normalizer_version=NORMALIZER_VERSION,
                    source_artifact_id=extraction.source_artifact_id,
                    source_artifact_type=extraction.source_artifact_type,
                    source_block_id=section.source_block_id,
                    source_path=section.source_path,
                )
                session.add(db_section)
                session.flush()

                for frag_order, fragment in enumerate(section.fragments):
                    if fragment.raw_html:
                        html_chunks.append(fragment.raw_html)
                    stable_id = self._make_stable_id(version_id, sec_order, frag_order, fragment.fragment_text)
                    db_frag = TextFragment(
                        section_id=db_section.id,
                        fragment_order=frag_order,
                        fragment_type=fragment.fragment_type,
                        fragment_text=fragment.fragment_text,
                        stable_id=stable_id,
                        source_artifact_id=extraction.source_artifact_id,
                        source_artifact_type=extraction.source_artifact_type,
                        source_block_id=fragment.source_block_id,
                        source_path=fragment.source_path,
                        content_kind=fragment.content_kind,
                    )
                    session.add(db_frag)
                    fragments_count += 1

            self._persist_cleaned_html_artifact(
                session,
                version=version,
                source_artifact_id=extraction.source_artifact_id,
                html_chunks=html_chunks,
            )
            if extraction.source_used == "json" and json_artifact is not None:
                self._persist_derived_blocks_artifact(
                    session,
                    version=version,
                    source_artifact=json_artifact,
                )

            session.commit()
            logger.info("Normalized version %d: %d sections", version_id, len(sections))

            # Queue extraction
            from app.workers.tasks.extract import extract_document

            extract_document.delay(version_id)
            return NormalizeServiceResult(
                version.registry_id,
                version_id,
                "success",
                sections_count=len(sections),
                fragments_count=fragments_count,
                source_used=extraction.source_used,
                queued_extract=True,
            )

        finally:
            session.close()

    def _extract_sections(
        self,
        version: DocumentVersion,
        json_artifact: SourceArtifact | None,
        html_artifact: SourceArtifact | None,
        pdf_artifact: SourceArtifact | None,
    ) -> list[tuple[str, str, list[tuple[str, str]]]]:
        """Extract sections using the preferred source, with PDF fallback for thin HTML shells."""
        candidates = self._extract_sections_detailed(version, json_artifact, html_artifact, pdf_artifact).sections
        return [
            (
                section.section_title,
                section.section_path,
                [(fragment.fragment_type, fragment.fragment_text) for fragment in section.fragments],
            )
            for section in candidates
        ]

    def _extract_sections_detailed(
        self,
        version: DocumentVersion,
        json_artifact: SourceArtifact | None,
        html_artifact: SourceArtifact | None,
        pdf_artifact: SourceArtifact | None,
    ) -> NormalizeExtractionResult:
        """Extract sections and keep the source/reason metadata for stage outcomes."""
        preferred_source = version.source_type_primary or ""

        if json_artifact:
            try:
                raw_data = download_artifact(json_artifact.raw_path)
                sections = self._normalize_json(raw_data)
                if sections:
                    return NormalizeExtractionResult(
                        sections=sections,
                        source_used="json",
                        source_artifact_id=getattr(json_artifact, "id", None),
                        source_artifact_type="json",
                    )
            except (UnicodeDecodeError, json.JSONDecodeError):
                logger.warning("JSON normalization parse failed for version %d", version.id)
                json_reason_code = "normalize_json_parse_failed"
            else:
                json_reason_code = "normalize_empty_after_json"
        else:
            json_reason_code = "normalize_json_no_blocks"

        if preferred_source == "pdf" and pdf_artifact:
            raw_data = download_artifact(pdf_artifact.raw_path)
            sections = self._tuple_sections_to_candidates(self._normalize_pdf(raw_data), "pdf")
            return NormalizeExtractionResult(
                sections=sections,
                source_used="pdf_fallback",
                reason_code=None if sections else "normalize_empty_after_pdf_fallback",
                source_artifact_id=getattr(pdf_artifact, "id", None),
                source_artifact_type="pdf",
            )

        if html_artifact:
            raw_data = download_artifact(html_artifact.raw_path)
            sections = self._tuple_sections_to_candidates(self._normalize_html(raw_data), "html")
            if sections:
                return NormalizeExtractionResult(
                    sections=sections,
                    source_used="html_fallback",
                    source_artifact_id=getattr(html_artifact, "id", None),
                    source_artifact_type="html",
                )
            if pdf_artifact:
                logger.info(
                    "HTML artifact produced no sections for version %d, falling back to PDF",
                    version.id,
                )
            else:
                return NormalizeExtractionResult(
                    sections=[],
                    source_used="html_fallback",
                    reason_code="normalize_empty_after_html",
                    source_artifact_id=getattr(html_artifact, "id", None),
                    source_artifact_type="html",
                )

        if pdf_artifact:
            raw_data = download_artifact(pdf_artifact.raw_path)
            sections = self._tuple_sections_to_candidates(self._normalize_pdf(raw_data), "pdf")
            return NormalizeExtractionResult(
                sections=sections,
                source_used="pdf_fallback",
                reason_code=None if sections else "normalize_empty_after_pdf_fallback",
                source_artifact_id=getattr(pdf_artifact, "id", None),
                source_artifact_type="pdf",
            )

        if json_artifact:
            return NormalizeExtractionResult(
                sections=[],
                source_used="json",
                reason_code=json_reason_code,
                source_artifact_id=getattr(json_artifact, "id", None),
                source_artifact_type="json",
            )
        return NormalizeExtractionResult(sections=[], reason_code="normalize_missing_artifact")

    def _tuple_sections_to_candidates(
        self,
        sections: list[tuple[str, str, list[tuple[str, str]]]],
        artifact_type: str,
    ) -> list[NormalizedSectionCandidate]:
        converted: list[NormalizedSectionCandidate] = []
        for sec_order, (section_title, section_path, fragments) in enumerate(sections):
            converted.append(
                NormalizedSectionCandidate(
                    section_title=section_title,
                    section_path=section_path,
                    fragments=[
                        NormalizedFragmentCandidate(
                            fragment_type=fragment_type,
                            fragment_text=fragment_text,
                            source_path=f"/{artifact_type}/sections/{sec_order}/fragments/{frag_order}",
                            content_kind="text",
                        )
                        for frag_order, (fragment_type, fragment_text) in enumerate(fragments)
                    ],
                    source_path=f"/{artifact_type}/sections/{sec_order}",
                )
            )
        return converted

    def _normalize_json(self, raw_data: bytes) -> list[NormalizedSectionCandidate]:
        payload = json.loads(raw_data.decode("utf-8"))
        blocks = collect_canonical_blocks(payload)
        if not blocks:
            return []

        sections: list[NormalizedSectionCandidate] = []
        for idx, block in enumerate(blocks):
            fragments: list[NormalizedFragmentCandidate] = []
            if block.rules is not None:
                rules_text = serialize_rules_to_text(block.rules)
                if rules_text:
                    fragments.append(
                        NormalizedFragmentCandidate(
                            fragment_type="paragraph",
                            fragment_text=rules_text,
                            source_block_id=block.block_id,
                            source_path=block.source_path,
                            content_kind="text",
                        )
                    )

            if block.html:
                html_text = BeautifulSoup(block.html, "lxml").get_text(" ", strip=True)
                if html_text:
                    fragments.append(
                        NormalizedFragmentCandidate(
                            fragment_type="html_block",
                            fragment_text=html_text,
                            source_block_id=block.block_id,
                            source_path=block.source_path,
                            content_kind="html",
                            raw_html=block.html,
                        )
                    )

            if block.image_ref:
                fragments.append(
                    NormalizedFragmentCandidate(
                        fragment_type="image_ref",
                        fragment_text=f"Image block: {block.image_ref}",
                        source_block_id=block.block_id,
                        source_path=block.source_path,
                        content_kind="image",
                    )
                )

            if block.table is not None:
                table_text = serialize_rules_to_text(block.table)
                if table_text:
                    fragments.append(
                        NormalizedFragmentCandidate(
                            fragment_type="table_row",
                            fragment_text=table_text,
                            source_block_id=block.block_id,
                            source_path=block.source_path,
                            content_kind="table_like",
                        )
                    )

            if not fragments and block.title:
                fragments.append(
                    NormalizedFragmentCandidate(
                        fragment_type="paragraph",
                        fragment_text=block.title,
                        source_block_id=block.block_id,
                        source_path=block.source_path,
                        content_kind="text",
                    )
                )

            if fragments:
                sections.append(
                    NormalizedSectionCandidate(
                        section_title=block.title or f"Section {idx + 1}",
                        section_path=block.source_path,
                        fragments=fragments,
                        source_block_id=block.block_id,
                        source_path=block.source_path,
                    )
                )

        return sections

    def _persist_cleaned_html_artifact(
        self,
        session,
        *,
        version: DocumentVersion,
        source_artifact_id: int | None,
        html_chunks: list[str],
    ) -> None:
        if not html_chunks:
            return
        merged_html = "\n".join(html_chunks)
        cleaned_html = sanitize_html(merged_html)
        if not cleaned_html.strip():
            return

        data = cleaned_html.encode("utf-8")
        data_hash = content_hash(data)
        existing = (
            session.query(SourceArtifact)
            .filter_by(
                document_version_id=version.id,
                artifact_type="cleaned_html",
                content_hash=data_hash,
            )
            .first()
        )
        if existing:
            return

        key = f"documents/{version.registry_id}/versions/{version.id}/cleaned_html.html"
        upload_artifact(data, key, "text/html")
        session.add(
            SourceArtifact(
                document_version_id=version.id,
                artifact_type="cleaned_html",
                raw_path=key,
                content_hash=data_hash,
                content_type="text/html",
                headers_json={
                    "derived_from_artifact_id": source_artifact_id,
                    "generator": "cleaned_html_v1",
                },
                fetched_at=datetime.now(timezone.utc),
            )
        )

    def _persist_derived_blocks_artifact(
        self,
        session,
        *,
        version: DocumentVersion,
        source_artifact: SourceArtifact,
    ) -> None:
        payload = json.loads(download_artifact(source_artifact.raw_path).decode("utf-8"))
        blocks = collect_canonical_blocks(payload)
        if not blocks:
            return

        derived_payload = {
            "schema_version": "canonical_json_blocks_v1",
            "source_artifact_id": source_artifact.id,
            "source_artifact_type": "json",
            "blocks": [
                {
                    "block_id": block.block_id,
                    "source_path": block.source_path,
                    "order": block.order,
                    "title": block.title,
                    "content_kind": block.content_kind,
                    "has_rules": block.rules is not None,
                    "has_html": bool(block.html),
                    "image_ref": block.image_ref,
                }
                for block in blocks
            ],
        }

        data = json.dumps(derived_payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        data_hash = content_hash(data)
        existing = (
            session.query(SourceArtifact)
            .filter_by(
                document_version_id=version.id,
                artifact_type="derived_blocks",
                content_hash=data_hash,
            )
            .first()
        )
        if existing:
            return

        key = f"documents/{version.registry_id}/versions/{version.id}/derived_blocks.json"
        upload_artifact(data, key, "application/json")
        session.add(
            SourceArtifact(
                document_version_id=version.id,
                artifact_type="derived_blocks",
                raw_path=key,
                content_hash=data_hash,
                content_type="application/json",
                headers_json={
                    "derived_from_artifact_id": source_artifact.id,
                    "generator": "canonical_json_blocks_v1",
                },
                fetched_at=datetime.now(timezone.utc),
            )
        )

    def _normalize_html(self, raw_data: bytes) -> list[tuple[str, str, list[tuple[str, str]]]]:
        """Parse HTML content into sections with fragments.

        Returns list of (section_title, section_path, [(fragment_type, fragment_text), ...])
        """
        html_text = raw_data.decode("utf-8", errors="replace")
        soup = BeautifulSoup(html_text, "lxml")

        # Remove noise elements
        for selector in NOISE_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        # Find the main content area
        content = (
            soup.find("main")
            or soup.find("article")
            or soup.find("div", class_=re.compile(r"content|document|text|body", re.I))
            or soup.find("body")
        )
        if not content:
            return []

        sections = []
        current_section_title = "Введение"
        current_section_path = "0"
        current_fragments: list[tuple[str, str]] = []
        section_counter = 0

        for element in content.descendants:
            if isinstance(element, Tag):
                # New section on heading elements
                if element.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    # Save previous section
                    if current_fragments:
                        sections.append((current_section_title, current_section_path, current_fragments))
                        current_fragments = []

                    section_counter += 1
                    level = int(element.name[1])
                    current_section_title = self._clean_text(element.get_text())
                    current_section_path = f"{section_counter}.{level}"

                elif element.name == "p":
                    text = self._clean_text(element.get_text())
                    if text:
                        current_fragments.append(("paragraph", text))

                elif element.name in ("li",):
                    text = self._clean_text(element.get_text())
                    if text:
                        current_fragments.append(("bullet", text))

                elif element.name in ("tr",):
                    cells = [self._clean_text(td.get_text()) for td in element.find_all(["td", "th"])]
                    row_text = " | ".join(c for c in cells if c)
                    if row_text:
                        current_fragments.append(("table_row", row_text))

                elif element.name in ("caption", "figcaption"):
                    text = self._clean_text(element.get_text())
                    if text:
                        current_fragments.append(("caption", text))

        # Save last section
        if current_fragments:
            sections.append((current_section_title, current_section_path, current_fragments))

        return sections

    def _normalize_pdf(self, raw_data: bytes) -> list[tuple[str, str, list[tuple[str, str]]]]:
        """Parse PDF content into sections with fragments."""
        try:
            import pdfplumber
        except ImportError:
            logger.error("pdfplumber not installed — cannot process PDF")
            return []

        import io

        sections = []
        current_section_title = "Документ"
        current_section_path = "0"
        current_fragments: list[tuple[str, str]] = []
        section_counter = 0

        try:
            with pdfplumber.open(io.BytesIO(raw_data)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    lines = text.split("\n")

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Heuristic: detect section headings
                        if self._looks_like_heading(line):
                            if current_fragments:
                                sections.append((current_section_title, current_section_path, current_fragments))
                                current_fragments = []
                            section_counter += 1
                            current_section_title = line
                            current_section_path = str(section_counter)
                        else:
                            # Detect bullet points
                            if re.match(r"^[\-•●◦▪]\s+", line):
                                frag_type = "bullet"
                                line = re.sub(r"^[\-•●◦▪]\s+", "", line)
                            elif re.match(r"^\d+\.\s+", line) and len(line) < 200:
                                frag_type = "bullet"
                            else:
                                frag_type = "paragraph"

                            cleaned = self._clean_text(line)
                            if cleaned:
                                current_fragments.append((frag_type, cleaned))

                    # Extract tables
                    tables = page.extract_tables() or []
                    for table in tables:
                        for row in table:
                            cells = [self._clean_text(c or "") for c in row]
                            row_text = " | ".join(c for c in cells if c)
                            if row_text:
                                current_fragments.append(("table_row", row_text))

        except Exception as e:
            logger.error("PDF parsing error: %s", e)
            return []

        if current_fragments:
            sections.append((current_section_title, current_section_path, current_fragments))

        return sections

    def _looks_like_heading(self, line: str) -> bool:
        """Heuristic: is this line likely a section heading?"""
        if len(line) > 200:
            return False
        if len(line) < 3:
            return False
        # Numbered section pattern
        if re.match(r"^\d+(\.\d+)*\.?\s+[А-ЯA-Z]", line):
            return True
        # All caps line
        if line == line.upper() and len(line) > 5 and len(line) < 100:
            return True
        return False

    def _clean_text(self, text: str) -> str:
        """Clean whitespace and normalize text."""
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _make_stable_id(self, version_id: int, sec_order: int, frag_order: int, text: str) -> str:
        """Create a stable fragment identifier."""
        raw = f"{version_id}:{sec_order}:{frag_order}:{text[:50]}"
        return hashlib.md5(raw.encode()).hexdigest()

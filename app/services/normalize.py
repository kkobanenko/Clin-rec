"""Normalize service — cleans raw HTML/PDF, splits into sections and fragments."""

import hashlib
import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup, NavigableString, Tag

from app.core.storage import download_artifact
from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion, SourceArtifact
from app.models.text import DocumentSection, TextFragment

logger = logging.getLogger(__name__)

NORMALIZER_VERSION = "1.0.0"

# Elements to remove from HTML before processing
NOISE_SELECTORS = [
    "nav", "header", "footer", ".cookie-banner", ".breadcrumb",
    ".navigation", ".sidebar", ".toolbar", "script", "style",
    "noscript", "iframe", ".modal", ".popup",
]


class NormalizeService:
    def normalize(self, version_id: int) -> bool:
        """Нормализует версию документа. Возвращает True если данные закоммичены."""
        session = get_sync_session()
        try:
            version = session.get(DocumentVersion, version_id)
            if not version:
                logger.error("DocumentVersion %d not found", version_id)
                return False

            # Remove old sections/fragments for this version
            old_sections = session.query(DocumentSection).filter_by(document_version_id=version_id).all()
            for sec in old_sections:
                session.query(TextFragment).filter_by(section_id=sec.id).delete()
                session.delete(sec)
            session.flush()

            # Get primary artifact
            artifacts = (
                session.query(SourceArtifact)
                .filter_by(document_version_id=version_id)
                .all()
            )

            html_artifact = next((a for a in artifacts if a.artifact_type == "html"), None)
            pdf_artifact = next((a for a in artifacts if a.artifact_type == "pdf"), None)

            sections = self._extract_sections(version, html_artifact, pdf_artifact)

            if not sections:
                logger.warning("No sections extracted for version %d", version_id)
                session.rollback()
                return False

            # Write to DB
            for sec_order, (sec_title, sec_path, fragments) in enumerate(sections):
                db_section = DocumentSection(
                    document_version_id=version_id,
                    section_path=sec_path,
                    section_title=sec_title,
                    section_order=sec_order,
                    normalizer_version=NORMALIZER_VERSION,
                )
                session.add(db_section)
                session.flush()

                for frag_order, (frag_type, frag_text) in enumerate(fragments):
                    stable_id = self._make_stable_id(version_id, sec_order, frag_order, frag_text)
                    db_frag = TextFragment(
                        section_id=db_section.id,
                        fragment_order=frag_order,
                        fragment_type=frag_type,
                        fragment_text=frag_text,
                        stable_id=stable_id,
                    )
                    session.add(db_frag)

            session.commit()
            logger.info("Normalized version %d: %d sections", version_id, len(sections))

            # Дальнейший pipeline: worker ставит chain compile_kb → extract.

            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _extract_sections(
        self,
        version: DocumentVersion,
        html_artifact: SourceArtifact | None,
        pdf_artifact: SourceArtifact | None,
    ) -> list[tuple[str, str, list[tuple[str, str]]]]:
        """Extract sections using the preferred source, with PDF fallback for thin HTML shells."""
        preferred_source = version.source_type_primary or ""

        if preferred_source == "pdf" and pdf_artifact:
            raw_data = download_artifact(pdf_artifact.raw_path)
            return self._normalize_pdf(raw_data)

        if html_artifact:
            raw_data = download_artifact(html_artifact.raw_path)
            sections = self._normalize_html(raw_data)
            if sections:
                return sections
            if pdf_artifact:
                logger.info(
                    "HTML artifact produced no sections for version %d, falling back to PDF",
                    version.id,
                )

        if pdf_artifact:
            raw_data = download_artifact(pdf_artifact.raw_path)
            return self._normalize_pdf(raw_data)

        return []

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

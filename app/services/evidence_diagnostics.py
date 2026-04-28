"""Evidence Density Diagnostics Service.

Classifies each document version's fragments into one of five evidence states:
  evidence_rows_present — ≥1 pair_evidence row attached to fragment
  healthy_empty_state   — extraction ran, but fewer than 2 MNNs in fragment
  degraded_routing      — content_kind=image or text tagged ocr_unavailable
  extraction_missing    — extraction stage never ran for parent version
  scoring_missing       — evidence exists but no scored matrix cell
  no_mnn                — extraction ran, zero MNN hits found in fragment

Usage:
    svc = EvidenceDiagnosticsService()
    state = svc.diagnose_version(version_id=42)
"""

from __future__ import annotations

import logging
from itertools import permutations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.sync_database import get_sync_session
from app.models.clinical import ClinicalContext
from app.models.evidence import MatrixCell, PairEvidence
from app.models.pipeline_event import PipelineEventLog
from app.models.text import DocumentSection, TextFragment
from app.schemas.diagnostics import (
    CorpusCoverageOut,
    EvidenceStateCountersOut,
    FragmentDiagnosticOut,
    VersionEvidenceStateOut,
)
from app.services.extraction.mnn_extractor import MnnExtractor
from app.services.extraction.relation_extractor import RelationExtractor

logger = logging.getLogger(__name__)

_STATE_EXPLANATION: dict[str, str] = {
    "evidence_rows_present": (
        "This version has pair evidence rows. Scoring and matrix building can proceed."
    ),
    "healthy_empty_state": (
        "Extraction ran successfully. No fragment contained two or more distinct MNN "
        "mentions, so no pair candidates were generated. This is expected for documents "
        "that do not list drug substitution options."
    ),
    "degraded_routing": (
        "One or more fragments are classified as image/ocr-unavailable. Text extraction "
        "was skipped for those fragments. Consider re-fetching with a text-capable source."
    ),
    "extraction_missing": (
        "The extraction stage has not run for this version. "
        "Trigger the 'extract' pipeline stage to populate evidence."
    ),
    "scoring_missing": (
        "Pair evidence rows exist but no scored MatrixCell has been computed. "
        "Run the 'score' stage to produce matrix cells."
    ),
    "no_mnn": (
        "Extraction ran but found zero MNN hits across all fragments. "
        "The document may not contain INN/MNN drug names recognisable by the dictionary."
    ),
    "unknown": "Evidence state could not be determined.",
}


class EvidenceDiagnosticsService:
    """Provides per-version and corpus-level evidence density diagnostics."""

    def __init__(self) -> None:
        self._mnn_extractor: MnnExtractor | None = None
        self._relation_extractor: RelationExtractor | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def diagnose_version(
        self,
        version_id: int,
        include_fragment_details: bool = True,
        max_fragment_details: int = 200,
    ) -> VersionEvidenceStateOut:
        """Return full evidence density state for a document version."""
        session = get_sync_session()
        try:
            return self._diagnose_version_in_session(
                session,
                version_id,
                include_fragment_details,
                max_fragment_details,
            )
        finally:
            session.close()

    def corpus_coverage(self) -> CorpusCoverageOut:
        """Return corpus-level evidence density across all current versions."""
        from app.models.document import DocumentVersion  # local import to avoid circular

        session = get_sync_session()
        try:
            current_versions = (
                session.query(DocumentVersion)
                .filter_by(is_current=True)
                .all()
            )
            counters = EvidenceStateCountersOut()
            total_pair = 0
            total_json_sections = 0
            total_json_fragments = 0
            total_ocr = 0
            versions_with_extraction = 0
            versions_with_evidence = 0
            versions_healthy_empty = 0
            versions_degraded = 0
            versions_extraction_missing = 0

            for ver in current_versions:
                state = self._diagnose_version_in_session(
                    session, ver.id,
                    include_fragment_details=False,
                )
                dominant = state.dominant_evidence_state
                total_pair += state.pair_evidence_total
                total_json_sections += state.sections_total  # approximation
                total_json_fragments += state.fragments_total
                total_ocr += state.fragments_ocr_unavailable

                if state.extraction_ran:
                    versions_with_extraction += 1
                if dominant == "evidence_rows_present":
                    versions_with_evidence += 1
                elif dominant == "healthy_empty_state":
                    versions_healthy_empty += 1
                elif dominant == "degraded_routing":
                    versions_degraded += 1
                elif dominant == "extraction_missing":
                    versions_extraction_missing += 1

                # Tally counters
                _bump_counter(counters, dominant)

            total = len(current_versions)
            coverage_pct = round(versions_with_extraction / total * 100, 1) if total else 0.0
            density_pct = round(versions_with_evidence / total * 100, 1) if total else 0.0

            return CorpusCoverageOut(
                total_current_versions=total,
                versions_with_extraction=versions_with_extraction,
                versions_with_evidence=versions_with_evidence,
                versions_healthy_empty=versions_healthy_empty,
                versions_degraded_routing=versions_degraded,
                versions_extraction_missing=versions_extraction_missing,
                total_pair_evidence_rows=total_pair,
                total_json_derived_sections=total_json_sections,
                total_json_derived_fragments=total_json_fragments,
                total_ocr_unavailable_fragments=total_ocr,
                coverage_pct=coverage_pct,
                evidence_density_pct=density_pct,
            )
        finally:
            session.close()

    def state_counters(self) -> EvidenceStateCountersOut:
        """Return lightweight state counters for release evidence docs."""
        from app.models.document import DocumentVersion  # local import

        session = get_sync_session()
        try:
            current_versions = (
                session.query(DocumentVersion)
                .filter_by(is_current=True)
                .all()
            )
            counters = EvidenceStateCountersOut()
            for ver in current_versions:
                state = self._diagnose_version_in_session(
                    session, ver.id, include_fragment_details=False
                )
                _bump_counter(counters, state.dominant_evidence_state)
            return counters
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _diagnose_version_in_session(
        self,
        session: Session,
        version_id: int,
        include_fragment_details: bool = True,
        max_fragment_details: int = 200,
    ) -> VersionEvidenceStateOut:
        from app.models.document import DocumentVersion  # local import

        ver = session.get(DocumentVersion, version_id)
        if ver is None:
            return VersionEvidenceStateOut(
                document_id=0,
                version_id=version_id,
                dominant_evidence_state="unknown",
                explanation=_STATE_EXPLANATION["unknown"],
            )

        # Check whether extraction ran
        extraction_ran = self._extraction_ran(session, version_id)

        # Load sections and fragments
        sections = (
            session.query(DocumentSection)
            .filter_by(document_version_id=version_id)
            .all()
        )
        sections_total = len(sections)

        all_fragment_ids: list[int] = []
        frag_objects_by_id: dict[int, TextFragment] = {}

        for sec in sections:
            frags = (
                session.query(TextFragment)
                .filter_by(section_id=sec.id)
                .all()
            )
            for f in frags:
                all_fragment_ids.append(f.id)
                frag_objects_by_id[f.id] = f

        fragments_total = len(all_fragment_ids)

        # Pair evidence counts per fragment
        evidence_counts: dict[int, int] = {}
        if all_fragment_ids:
            rows = (
                session.query(
                    PairEvidence.fragment_id,
                    func.count(PairEvidence.id).label("cnt"),
                )
                .filter(PairEvidence.fragment_id.in_(all_fragment_ids))
                .group_by(PairEvidence.fragment_id)
                .all()
            )
            for frag_id, cnt in rows:
                evidence_counts[frag_id] = cnt

        pair_evidence_total = sum(evidence_counts.values())

        # Context count
        contexts_total = (
            session.query(func.count(ClinicalContext.id))
            .filter_by(document_version_id=version_id)
            .scalar()
        ) or 0

        # Per-fragment diagnostics
        fragment_diags: list[FragmentDiagnosticOut] = []
        fragments_with_mnn = 0
        fragments_ocr_unavailable = 0
        fragments_no_mnn = 0

        frag_items = all_fragment_ids[:max_fragment_details] if include_fragment_details else []

        # Always tally for dominant-state calc even if not returning details
        tally_frag_ids = all_fragment_ids

        for frag_id in tally_frag_ids:
            frag = frag_objects_by_id[frag_id]
            ck = (frag.content_kind or "text").strip().lower()

            is_ocr = ck == "image"
            if is_ocr:
                fragments_ocr_unavailable += 1

            ev_count = evidence_counts.get(frag_id, 0)

            # Determine per-fragment state
            if not extraction_ran:
                frag_state = "extraction_missing"
                reason = "Extraction stage not run."
            elif ev_count > 0:
                frag_state = "evidence_rows_present"
                reason = f"{ev_count} evidence row(s) attached."
            elif is_ocr:
                frag_state = "degraded_routing"
                reason = "content_kind=image; text extraction skipped."
            else:
                # Lazy-load MNN extractor only when needed
                if self._mnn_extractor is None:
                    self._mnn_extractor = MnnExtractor()
                    self._mnn_extractor.load_dictionary()
                text = (frag.fragment_text or "").strip()
                mnn_hits = self._mnn_extractor.extract(text) if text else []
                mol_count = len({h["molecule_id"] for h in mnn_hits})
                if mol_count >= 2:
                    fragments_with_mnn += 1
                    frag_state = "healthy_empty_state"
                    reason = (
                        f"{mol_count} MNN found but no candidates generated "
                        f"(no matching context or pair already exists)."
                    )
                else:
                    fragments_no_mnn += 1
                    frag_state = "no_mnn"
                    reason = f"Only {mol_count} MNN found; need ≥2 for pair generation."

            if include_fragment_details and frag_id in frag_items:
                text_preview = (frag.fragment_text or "")[:120]
                fragment_diags.append(
                    FragmentDiagnosticOut(
                        fragment_id=frag.id,
                        section_id=frag.section_id,
                        content_kind=ck,
                        source_artifact_type=frag.source_artifact_type,
                        source_block_id=frag.source_block_id,
                        fragment_text_preview=text_preview,
                        evidence_rows=ev_count,
                        evidence_state=frag_state,
                        reason_detail=reason,
                    )
                )

        # Determine dominant state
        if not extraction_ran:
            dominant = "extraction_missing"
        elif pair_evidence_total > 0:
            dominant = "evidence_rows_present"
        elif fragments_ocr_unavailable > (fragments_total * 0.5 if fragments_total else 0):
            dominant = "degraded_routing"
        elif fragments_with_mnn > 0:
            dominant = "healthy_empty_state"
        elif fragments_no_mnn > 0:
            dominant = "no_mnn"
        else:
            dominant = "healthy_empty_state"

        # Dominant artifact type from sections
        artifact_types: dict[str, int] = {}
        for sec in sections:
            at = sec.source_artifact_type or "unknown"
            artifact_types[at] = artifact_types.get(at, 0) + 1
        dominant_artifact = max(artifact_types, key=artifact_types.get) if artifact_types else None

        return VersionEvidenceStateOut(
            document_id=ver.registry_id,
            version_id=version_id,
            extraction_ran=extraction_ran,
            sections_total=sections_total,
            fragments_total=fragments_total,
            fragments_with_mnn=fragments_with_mnn,
            fragments_ocr_unavailable=fragments_ocr_unavailable,
            fragments_no_mnn=fragments_no_mnn,
            pair_evidence_total=pair_evidence_total,
            contexts_total=contexts_total,
            dominant_evidence_state=dominant,
            source_artifact_type_dominant=dominant_artifact,
            fragment_diagnostics=fragment_diags if include_fragment_details else [],
            explanation=_STATE_EXPLANATION.get(dominant, _STATE_EXPLANATION["unknown"]),
        )

    @staticmethod
    def _extraction_ran(session: Session, version_id: int) -> bool:
        """Return True if at least one successful extraction pipeline event exists."""
        row = (
            session.query(PipelineEventLog)
            .filter(
                PipelineEventLog.document_version_id == version_id,
                PipelineEventLog.stage == "extract",
                PipelineEventLog.status == "success",
            )
            .first()
        )
        return row is not None


def _bump_counter(counters: EvidenceStateCountersOut, state: str) -> None:
    """Increment the named field on EvidenceStateCountersOut in-place."""
    field = state if state in {
        "evidence_rows_present",
        "healthy_empty_state",
        "degraded_routing",
        "extraction_missing",
        "scoring_missing",
        "no_mnn",
    } else "unknown"
    setattr(counters, field, getattr(counters, field, 0) + 1)

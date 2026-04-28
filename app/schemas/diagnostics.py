"""Diagnostic schemas — evidence density and fragment extraction observability."""

from __future__ import annotations

from pydantic import BaseModel


class FragmentDiagnosticOut(BaseModel):
    """Per-fragment evidence pipeline state."""

    fragment_id: int
    section_id: int
    content_kind: str | None = None
    source_artifact_type: str | None = None
    source_block_id: str | None = None
    fragment_text_preview: str | None = None  # first 120 chars
    mnn_hits: int = 0
    context_candidates: int = 0
    relation_signals: int = 0
    evidence_rows: int = 0
    evidence_state: str = "unknown"
    # possible values:
    #   evidence_rows_present  — ≥1 pair_evidence row attached to this fragment
    #   healthy_empty_state    — extraction ran, MNN found < 2 in this fragment
    #   degraded_routing       — content_kind=image or ocr_unavailable
    #   extraction_missing     — extraction stage never ran for parent version
    #   scoring_missing        — evidence exists but no scored matrix cell
    #   no_mnn                 — extraction ran, zero MNN hits in fragment
    reason_detail: str | None = None


class VersionEvidenceStateOut(BaseModel):
    """Aggregated evidence density state for a single document version."""

    document_id: int
    version_id: int
    extraction_ran: bool = False
    sections_total: int = 0
    fragments_total: int = 0
    fragments_with_mnn: int = 0
    fragments_ocr_unavailable: int = 0
    fragments_no_mnn: int = 0
    pair_evidence_total: int = 0
    contexts_total: int = 0
    dominant_evidence_state: str = "unknown"
    # possible values (same as FragmentDiagnosticOut.evidence_state):
    #   evidence_rows_present
    #   healthy_empty_state
    #   degraded_routing
    #   extraction_missing
    #   scoring_missing
    #   no_mnn
    source_artifact_type_dominant: str | None = None
    fragment_diagnostics: list[FragmentDiagnosticOut] = []
    explanation: str = ""


class CorpusCoverageOut(BaseModel):
    """Corpus-level evidence density summary across all current versions."""

    total_current_versions: int = 0
    versions_with_extraction: int = 0
    versions_with_evidence: int = 0
    versions_healthy_empty: int = 0
    versions_degraded_routing: int = 0
    versions_extraction_missing: int = 0
    total_pair_evidence_rows: int = 0
    total_json_derived_sections: int = 0
    total_json_derived_fragments: int = 0
    total_ocr_unavailable_fragments: int = 0
    coverage_pct: float = 0.0
    evidence_density_pct: float = 0.0


class EvidenceStateCountersOut(BaseModel):
    """Lightweight evidence state counters for release evidence documents."""

    evidence_rows_present: int = 0
    healthy_empty_state: int = 0
    degraded_routing: int = 0
    extraction_missing: int = 0
    scoring_missing: int = 0
    no_mnn: int = 0
    unknown: int = 0

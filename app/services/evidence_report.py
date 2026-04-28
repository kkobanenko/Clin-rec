"""Release Evidence Report Service.

Generates structured release evidence documents combining runtime metrics,
artifact coverage, fragment traceability, and evidence density state.

This service is additive — it reads from existing tables and does not write
anything to the database.

Usage:
    svc = ReleaseEvidenceReportService()
    report = svc.generate_report()
    print(report.to_markdown())
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.sync_database import get_sync_session
from app.models.document import DocumentVersion, SourceArtifact
from app.models.evidence import PairEvidence, MatrixCell
from app.models.scoring import ScoringModelVersion
from app.models.text import DocumentSection, TextFragment
from app.schemas.diagnostics import EvidenceStateCountersOut
from app.services.evidence_diagnostics import EvidenceDiagnosticsService

logger = logging.getLogger(__name__)


@dataclass
class ArtifactCoverageRow:
    artifact_type: str
    count: int
    pct_of_versions: float


@dataclass
class SampleTraceabilityChain:
    """A single sample traceability chain from source artifact to fragment."""
    version_id: int
    section_id: int
    fragment_id: int
    source_artifact_type: str | None
    source_block_id: str | None
    content_kind: str | None
    fragment_text_preview: str | None


@dataclass
class ReleaseEvidenceReport:
    """Structured release evidence report."""
    generated_at: datetime
    current_versions_total: int = 0
    versions_with_json_artifact: int = 0
    versions_with_normalized_content: int = 0
    json_derived_sections: int = 0
    json_derived_fragments: int = 0
    total_pair_evidence_rows: int = 0
    total_matrix_cells: int = 0
    active_model_version: str | None = None
    artifact_coverage: list[ArtifactCoverageRow] = field(default_factory=list)
    evidence_state_counters: EvidenceStateCountersOut = field(
        default_factory=EvidenceStateCountersOut
    )
    sample_chains: list[SampleTraceabilityChain] = field(default_factory=list)
    known_limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at.isoformat(),
            "current_versions_total": self.current_versions_total,
            "versions_with_json_artifact": self.versions_with_json_artifact,
            "versions_with_normalized_content": self.versions_with_normalized_content,
            "json_derived_sections": self.json_derived_sections,
            "json_derived_fragments": self.json_derived_fragments,
            "total_pair_evidence_rows": self.total_pair_evidence_rows,
            "total_matrix_cells": self.total_matrix_cells,
            "active_model_version": self.active_model_version,
            "artifact_coverage": [
                {
                    "artifact_type": r.artifact_type,
                    "count": r.count,
                    "pct_of_versions": r.pct_of_versions,
                }
                for r in self.artifact_coverage
            ],
            "evidence_state_counters": {
                "evidence_rows_present": self.evidence_state_counters.evidence_rows_present,
                "healthy_empty_state": self.evidence_state_counters.healthy_empty_state,
                "degraded_routing": self.evidence_state_counters.degraded_routing,
                "extraction_missing": self.evidence_state_counters.extraction_missing,
                "scoring_missing": self.evidence_state_counters.scoring_missing,
                "no_mnn": self.evidence_state_counters.no_mnn,
                "unknown": self.evidence_state_counters.unknown,
            },
            "sample_chains": [
                {
                    "version_id": c.version_id,
                    "section_id": c.section_id,
                    "fragment_id": c.fragment_id,
                    "source_artifact_type": c.source_artifact_type,
                    "source_block_id": c.source_block_id,
                    "content_kind": c.content_kind,
                    "fragment_text_preview": c.fragment_text_preview,
                }
                for c in self.sample_chains
            ],
            "known_limitations": self.known_limitations,
        }

    def to_markdown(self) -> str:
        """Render report as a Markdown document."""
        lines: list[str] = []
        ts = self.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"# Release Evidence Report — {ts}\n")

        lines.append("## Document Corpus\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|---|---:|")
        lines.append(f"| Current versions | {self.current_versions_total} |")
        lines.append(f"| Versions with JSON artifact | {self.versions_with_json_artifact} |")
        lines.append(f"| Versions with normalized content | {self.versions_with_normalized_content} |")
        lines.append(f"| JSON-derived sections | {self.json_derived_sections} |")
        lines.append(f"| JSON-derived fragments | {self.json_derived_fragments} |")
        lines.append(f"| Total pair evidence rows | {self.total_pair_evidence_rows} |")
        lines.append(f"| Total matrix cells | {self.total_matrix_cells} |")
        if self.active_model_version:
            lines.append(f"| Active scoring model | {self.active_model_version} |")
        lines.append("")

        if self.artifact_coverage:
            lines.append("## Artifact Coverage\n")
            lines.append("| Artifact Type | Count | % of versions |")
            lines.append("|---|---:|---:|")
            for row in self.artifact_coverage:
                lines.append(f"| {row.artifact_type} | {row.count} | {row.pct_of_versions:.1f}% |")
            lines.append("")

        lines.append("## Evidence State Distribution\n")
        ec = self.evidence_state_counters
        lines.append("| State | Count |")
        lines.append("|---|---:|")
        lines.append(f"| evidence_rows_present | {ec.evidence_rows_present} |")
        lines.append(f"| healthy_empty_state | {ec.healthy_empty_state} |")
        lines.append(f"| degraded_routing | {ec.degraded_routing} |")
        lines.append(f"| extraction_missing | {ec.extraction_missing} |")
        lines.append(f"| scoring_missing | {ec.scoring_missing} |")
        lines.append(f"| no_mnn | {ec.no_mnn} |")
        lines.append(f"| unknown | {ec.unknown} |")
        lines.append("")

        if self.sample_chains:
            lines.append("## Sample Traceability Chains\n")
            for i, c in enumerate(self.sample_chains, 1):
                lines.append(f"### Sample {i}")
                lines.append(f"- **version_id**: {c.version_id}")
                lines.append(f"- **section_id**: {c.section_id}")
                lines.append(f"- **fragment_id**: {c.fragment_id}")
                lines.append(f"- **source_artifact_type**: {c.source_artifact_type}")
                lines.append(f"- **source_block_id**: {c.source_block_id}")
                lines.append(f"- **content_kind**: {c.content_kind}")
                if c.fragment_text_preview:
                    lines.append(f"- **text preview**: `{c.fragment_text_preview[:80]}`")
                lines.append("")

        if self.known_limitations:
            lines.append("## Known Limitations\n")
            for lim in self.known_limitations:
                lines.append(f"- {lim}")
            lines.append("")

        return "\n".join(lines)


class ReleaseEvidenceReportService:
    """Generates structured release evidence reports for current-head state."""

    _DEFAULT_LIMITATIONS = [
        "Evidence density depends on MNN dictionary coverage; INN names not in dictionary will not generate evidence.",
        "OCR-unavailable fragments (content_kind=image) cannot contribute pair evidence without OCR support.",
        "healthy_empty_state is expected for clinical documents that do not compare drug alternatives.",
        "extraction_missing state requires a successful 'extract' pipeline stage run per version.",
    ]

    def generate_report(
        self,
        max_sample_chains: int = 5,
        include_state_counters: bool = True,
    ) -> ReleaseEvidenceReport:
        """Generate a full release evidence report for all current versions."""
        session = get_sync_session()
        try:
            # Current versions
            current_versions = (
                session.query(DocumentVersion)
                .filter_by(is_current=True)
                .all()
            )
            total = len(current_versions)
            version_ids = [v.id for v in current_versions]

            # JSON artifact coverage
            versions_with_json = 0
            artifact_type_counts: dict[str, int] = {}
            if version_ids:
                artifacts = (
                    session.query(SourceArtifact)
                    .filter(SourceArtifact.document_version_id.in_(version_ids))
                    .all()
                )
                seen_json_versions: set[int] = set()
                for art in artifacts:
                    at = art.artifact_type
                    artifact_type_counts[at] = artifact_type_counts.get(at, 0) + 1
                    if at == "json" and art.document_version_id not in seen_json_versions:
                        seen_json_versions.add(art.document_version_id)
                        versions_with_json += 1

            # Normalized content counts
            json_sections = 0
            json_fragments = 0
            versions_with_content = 0
            for ver in current_versions:
                secs = (
                    session.query(DocumentSection)
                    .filter_by(document_version_id=ver.id)
                    .all()
                )
                if not secs:
                    continue
                versions_with_content += 1
                for sec in secs:
                    if sec.source_artifact_type == "json":
                        json_sections += 1
                    frags = (
                        session.query(TextFragment)
                        .filter_by(section_id=sec.id)
                        .all()
                    )
                    for frag in frags:
                        if frag.source_artifact_type == "json":
                            json_fragments += 1

            # Pair evidence and matrix cells
            total_pe = session.query(PairEvidence).count() or 0
            total_mc = session.query(MatrixCell).count() or 0

            # Active scoring model
            active_model = (
                session.query(ScoringModelVersion)
                .filter(ScoringModelVersion.is_active.is_(True))
                .order_by(ScoringModelVersion.created_at.desc())
                .first()
            )
            active_model_label = active_model.version_label if active_model else None

            # Artifact coverage rows
            coverage_rows = [
                ArtifactCoverageRow(
                    artifact_type=at,
                    count=cnt,
                    pct_of_versions=round(cnt / total * 100, 1) if total else 0.0,
                )
                for at, cnt in sorted(artifact_type_counts.items())
            ]

            # Sample traceability chains
            sample_chains: list[SampleTraceabilityChain] = []
            for ver in current_versions[:max_sample_chains]:
                secs = (
                    session.query(DocumentSection)
                    .filter_by(document_version_id=ver.id)
                    .limit(1)
                    .all()
                )
                if not secs:
                    continue
                sec = secs[0]
                frags = (
                    session.query(TextFragment)
                    .filter_by(section_id=sec.id)
                    .limit(1)
                    .all()
                )
                if not frags:
                    continue
                frag = frags[0]
                sample_chains.append(
                    SampleTraceabilityChain(
                        version_id=ver.id,
                        section_id=sec.id,
                        fragment_id=frag.id,
                        source_artifact_type=frag.source_artifact_type,
                        source_block_id=frag.source_block_id,
                        content_kind=frag.content_kind,
                        fragment_text_preview=(frag.fragment_text or "")[:80],
                    )
                )

        finally:
            session.close()

        # Evidence state counters (uses a separate service)
        state_counters = EvidenceStateCountersOut()
        if include_state_counters:
            try:
                diag_svc = EvidenceDiagnosticsService()
                state_counters = diag_svc.state_counters()
            except Exception as exc:  # noqa: BLE001 — never crash a report
                logger.warning("Could not compute evidence state counters: %s", exc)

        return ReleaseEvidenceReport(
            generated_at=datetime.now(tz=timezone.utc),
            current_versions_total=total,
            versions_with_json_artifact=versions_with_json,
            versions_with_normalized_content=versions_with_content,
            json_derived_sections=json_sections,
            json_derived_fragments=json_fragments,
            total_pair_evidence_rows=total_pe,
            total_matrix_cells=total_mc,
            active_model_version=active_model_label,
            artifact_coverage=coverage_rows,
            evidence_state_counters=state_counters,
            sample_chains=sample_chains,
            known_limitations=list(self._DEFAULT_LIMITATIONS),
        )

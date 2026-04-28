"""Corpus quality metrics service.

Provides a unified, DB-backed view of corpus completeness, evidence
richness, and scoring readiness across all ingest artifact types.
Intended for operator dashboards, release gates, and CI health checks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.core.sync_database import get_sync_session
from app.models.evidence import MatrixCell, PairEvidence
from app.models.scoring import ScoringModelVersion
from app.models.text import DocumentSection, TextFragment

logger = logging.getLogger(__name__)

# ── Thresholds used to classify corpus health ─────────────────────────────────
# Each threshold is expressed as a fraction (0.0–1.0) of the relevant total.

_DEFAULT_THRESHOLDS: dict[str, float] = {
    # What fraction of fragments must have at least one PairEvidence row
    "evidence_coverage_min": 0.05,
    # What fraction of fragments with evidence must also have a ScoreResult row
    "scoring_coverage_min": 0.80,
    # Image fragments above this fraction of the corpus flag "image-heavy"
    "image_fraction_warn": 0.40,
    # Unknown/null content_kind above this fraction flags "normalisation gap"
    "unknown_kind_warn": 0.20,
}


# ── Data-transfer objects ─────────────────────────────────────────────────────


@dataclass
class ContentKindBreakdown:
    """Fragment counts broken down by ``content_kind``."""

    text: int = 0
    html: int = 0
    table_like: int = 0
    image: int = 0
    unknown: int = 0
    total: int = 0

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "html": self.html,
            "table_like": self.table_like,
            "image": self.image,
            "unknown": self.unknown,
            "total": self.total,
        }


@dataclass
class EvidenceRichnessReport:
    """Evidence and scoring coverage for the whole corpus."""

    fragments_total: int = 0
    fragments_with_evidence: int = 0
    fragments_scored: int = 0
    pair_evidence_total: int = 0
    pair_evidence_scored: int = 0  # rows where final_fragment_score IS NOT NULL
    matrix_cell_total: int = 0
    active_model_version_id: Optional[int] = None

    @property
    def evidence_coverage_pct(self) -> float:
        if self.fragments_total == 0:
            return 0.0
        return round(self.fragments_with_evidence / self.fragments_total * 100, 2)

    @property
    def scoring_coverage_pct(self) -> float:
        if self.fragments_with_evidence == 0:
            return 0.0
        return round(self.fragments_scored / self.fragments_with_evidence * 100, 2)

    def to_dict(self) -> dict:
        return {
            "fragments_total": self.fragments_total,
            "fragments_with_evidence": self.fragments_with_evidence,
            "fragments_scored": self.fragments_scored,
            "pair_evidence_total": self.pair_evidence_total,
            "pair_evidence_scored": self.pair_evidence_scored,
            "matrix_cell_total": self.matrix_cell_total,
            "active_model_version_id": self.active_model_version_id,
            "evidence_coverage_pct": self.evidence_coverage_pct,
            "scoring_coverage_pct": self.scoring_coverage_pct,
        }


@dataclass
class CorpusQualityFlag:
    """A warning/info flag raised when a metric crosses a threshold."""

    severity: str  # "warn" | "info" | "ok"
    metric: str
    value: float
    threshold: float
    message: str

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "metric": self.metric,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
        }


@dataclass
class CorpusQualityReport:
    """Top-level report produced by :class:`CorpusQualityService`."""

    content_kind: ContentKindBreakdown = field(default_factory=ContentKindBreakdown)
    richness: EvidenceRichnessReport = field(default_factory=EvidenceRichnessReport)
    flags: list[CorpusQualityFlag] = field(default_factory=list)
    overall_health: str = "unknown"  # "healthy" | "degraded" | "critical" | "empty" | "unknown"

    def to_dict(self) -> dict:
        return {
            "overall_health": self.overall_health,
            "content_kind": self.content_kind.to_dict(),
            "richness": self.richness.to_dict(),
            "flags": [f.to_dict() for f in self.flags],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Corpus Quality Report",
            "",
            f"**Overall health:** {self.overall_health.upper()}",
            "",
            "## Content-Kind Breakdown",
            "",
            f"| Kind | Count |",
            f"|------|-------|",
            f"| text | {self.content_kind.text} |",
            f"| html | {self.content_kind.html} |",
            f"| table_like | {self.content_kind.table_like} |",
            f"| image | {self.content_kind.image} |",
            f"| unknown | {self.content_kind.unknown} |",
            f"| **total** | **{self.content_kind.total}** |",
            "",
            "## Evidence & Scoring Richness",
            "",
            f"- Fragments with evidence: **{self.richness.fragments_with_evidence}** "
            f"/ {self.richness.fragments_total} "
            f"({self.richness.evidence_coverage_pct}%)",
            f"- Fragments scored: **{self.richness.fragments_scored}** "
            f"/ {self.richness.fragments_with_evidence} "
            f"({self.richness.scoring_coverage_pct}%)",
            f"- Pair evidence rows: {self.richness.pair_evidence_total}",
            f"- Pair evidence scored: {self.richness.pair_evidence_scored}",
            f"- Matrix cell rows: {self.richness.matrix_cell_total}",
        ]
        if self.flags:
            lines += ["", "## Quality Flags", ""]
            for flag in self.flags:
                icon = "⚠️" if flag.severity == "warn" else "ℹ️"
                lines.append(f"- {icon} **{flag.metric}**: {flag.message}")
        return "\n".join(lines)


# ── Service ───────────────────────────────────────────────────────────────────


class CorpusQualityService:
    """Compute corpus quality metrics from the live database."""

    def __init__(self, thresholds: Optional[dict[str, float]] = None):
        self._thresholds = {**_DEFAULT_THRESHOLDS, **(thresholds or {})}

    # ------------------------------------------------------------------ public

    def generate_report(self) -> CorpusQualityReport:
        """Return a :class:`CorpusQualityReport` for the entire corpus."""
        session = get_sync_session()
        try:
            ck = self._content_kind_breakdown(session)
            richness = self._evidence_richness(session)
            flags = self._evaluate_flags(ck, richness)
            health = self._overall_health(ck, richness, flags)
            return CorpusQualityReport(
                content_kind=ck,
                richness=richness,
                flags=flags,
                overall_health=health,
            )
        finally:
            session.close()

    # ----------------------------------------------------------------- private

    def _content_kind_breakdown(self, session) -> ContentKindBreakdown:
        rows = (
            session.query(TextFragment.content_kind)
            .all()
        )
        ck = ContentKindBreakdown()
        for (kind,) in rows:
            ck.total += 1
            if kind == "text":
                ck.text += 1
            elif kind == "html":
                ck.html += 1
            elif kind == "table_like":
                ck.table_like += 1
            elif kind == "image":
                ck.image += 1
            else:
                ck.unknown += 1
        return ck

    def _evidence_richness(self, session) -> EvidenceRichnessReport:
        report = EvidenceRichnessReport()

        report.fragments_total = session.query(TextFragment).count()
        report.pair_evidence_total = session.query(PairEvidence).count()

        # Fragment IDs that have at least one PairEvidence row
        fragment_ids_with_evidence: set[int] = {
            fid
            for (fid,) in session.query(PairEvidence.fragment_id)
            .filter(PairEvidence.fragment_id.isnot(None))
            .distinct()
            .all()
        }
        report.fragments_with_evidence = len(fragment_ids_with_evidence)

        # PairEvidence rows that have been scored (final_fragment_score IS NOT NULL)
        report.pair_evidence_scored = (
            session.query(PairEvidence)
            .filter(PairEvidence.final_fragment_score.isnot(None))
            .count()
        )

        # Fragments that have at least one scored PairEvidence row
        scored_fragment_ids: set[int] = {
            fid
            for (fid,) in session.query(PairEvidence.fragment_id)
            .filter(
                PairEvidence.final_fragment_score.isnot(None),
                PairEvidence.fragment_id.isnot(None),
            )
            .distinct()
            .all()
        }
        report.fragments_scored = len(
            fragment_ids_with_evidence & scored_fragment_ids
        )

        # Active scoring model — drives matrix cell count
        active_model = (
            session.query(ScoringModelVersion)
            .filter(ScoringModelVersion.is_active.is_(True))
            .order_by(
                ScoringModelVersion.created_at.desc(),
                ScoringModelVersion.id.desc(),
            )
            .first()
        )
        if active_model is not None:
            report.active_model_version_id = active_model.id
            report.matrix_cell_total = (
                session.query(MatrixCell)
                .filter_by(model_version_id=active_model.id)
                .count()
            )

        return report

    def _evaluate_flags(
        self,
        ck: ContentKindBreakdown,
        richness: EvidenceRichnessReport,
    ) -> list[CorpusQualityFlag]:
        flags: list[CorpusQualityFlag] = []
        t = self._thresholds

        # Evidence coverage
        cov_frac = richness.fragments_with_evidence / max(richness.fragments_total, 1)
        min_cov = t["evidence_coverage_min"]
        if cov_frac < min_cov:
            flags.append(
                CorpusQualityFlag(
                    severity="warn",
                    metric="evidence_coverage",
                    value=round(cov_frac, 4),
                    threshold=min_cov,
                    message=(
                        f"Only {richness.fragments_with_evidence}/{richness.fragments_total} "
                        f"fragments ({cov_frac * 100:.1f}%) have evidence — "
                        f"min expected {min_cov * 100:.0f}%"
                    ),
                )
            )

        # Scoring coverage
        scored_frac = richness.fragments_scored / max(richness.fragments_with_evidence, 1)
        min_scored = t["scoring_coverage_min"]
        if richness.fragments_with_evidence > 0 and scored_frac < min_scored:
            flags.append(
                CorpusQualityFlag(
                    severity="warn",
                    metric="scoring_coverage",
                    value=round(scored_frac, 4),
                    threshold=min_scored,
                    message=(
                        f"Only {richness.fragments_scored}/{richness.fragments_with_evidence} "
                        f"evidence-bearing fragments are scored "
                        f"({scored_frac * 100:.1f}%) — min expected {min_scored * 100:.0f}%"
                    ),
                )
            )

        # Image fraction
        image_frac = ck.image / max(ck.total, 1)
        img_warn = t["image_fraction_warn"]
        if image_frac >= img_warn:
            flags.append(
                CorpusQualityFlag(
                    severity="warn",
                    metric="image_fraction",
                    value=round(image_frac, 4),
                    threshold=img_warn,
                    message=(
                        f"Image fragments are {image_frac * 100:.1f}% of corpus "
                        f"(≥{img_warn * 100:.0f}%); evidence extraction is skipped for images"
                    ),
                )
            )

        # Unknown content_kind
        unk_frac = ck.unknown / max(ck.total, 1)
        unk_warn = t["unknown_kind_warn"]
        if unk_frac >= unk_warn:
            flags.append(
                CorpusQualityFlag(
                    severity="warn",
                    metric="unknown_content_kind",
                    value=round(unk_frac, 4),
                    threshold=unk_warn,
                    message=(
                        f"{ck.unknown} fragments ({unk_frac * 100:.1f}%) have unknown "
                        "content_kind; normalisation step may need attention"
                    ),
                )
            )

        return flags

    @staticmethod
    def _overall_health(
        ck: ContentKindBreakdown,
        richness: EvidenceRichnessReport,
        flags: list[CorpusQualityFlag],
    ) -> str:
        if ck.total == 0:
            return "empty"
        warn_count = sum(1 for f in flags if f.severity == "warn")
        if warn_count == 0:
            return "healthy"
        if warn_count == 1:
            return "degraded"
        return "critical"

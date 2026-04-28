"""Aggregate candidate generation diagnostics from pipeline event logs.

This service reads successful ``extract`` events from ``pipeline_event_log`` and
produces a concise operator-facing report with corpus-level rates and recent
per-version diagnostics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from app.core.sync_database import get_sync_session
from app.models.pipeline_event import PipelineEventLog


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass
class CandidateVersionDiagnostic:
    """Candidate diagnostics captured for a single document version."""

    event_id: int
    created_at: str
    document_registry_id: int
    document_version_id: int
    candidate_pairs_count: int
    candidate_skip_rate: float
    candidate_fragments_no_mnn: int
    candidate_fragments_single_mnn: int
    candidate_fragments_image: int
    version_score_contexts_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "created_at": self.created_at,
            "document_registry_id": self.document_registry_id,
            "document_version_id": self.document_version_id,
            "candidate_pairs_count": self.candidate_pairs_count,
            "candidate_skip_rate": round(self.candidate_skip_rate, 4),
            "candidate_fragments_no_mnn": self.candidate_fragments_no_mnn,
            "candidate_fragments_single_mnn": self.candidate_fragments_single_mnn,
            "candidate_fragments_image": self.candidate_fragments_image,
            "version_score_contexts_count": self.version_score_contexts_count,
        }


@dataclass
class CandidateDiagnosticsReport:
    """Operator-facing aggregate report over recent extract diagnostics."""

    versions_considered: int = 0
    versions_with_candidate_pairs: int = 0
    avg_skip_rate: float = 0.0
    max_skip_rate: float = 0.0
    high_skip_versions: int = 0
    total_candidate_pairs: int = 0
    total_fragments_no_mnn: int = 0
    total_fragments_single_mnn: int = 0
    total_fragments_image: int = 0
    top_versions_by_skip_rate: list[CandidateVersionDiagnostic] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "versions_considered": self.versions_considered,
            "versions_with_candidate_pairs": self.versions_with_candidate_pairs,
            "versions_without_candidate_pairs": max(
                0,
                self.versions_considered - self.versions_with_candidate_pairs,
            ),
            "avg_skip_rate": round(self.avg_skip_rate, 4),
            "max_skip_rate": round(self.max_skip_rate, 4),
            "high_skip_versions": self.high_skip_versions,
            "total_candidate_pairs": self.total_candidate_pairs,
            "total_fragments_no_mnn": self.total_fragments_no_mnn,
            "total_fragments_single_mnn": self.total_fragments_single_mnn,
            "total_fragments_image": self.total_fragments_image,
            "top_versions_by_skip_rate": [item.to_dict() for item in self.top_versions_by_skip_rate],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Candidate Diagnostics Report",
            "",
            "## Summary",
            f"- Versions considered: **{self.versions_considered}**",
            f"- Versions with candidate pairs: **{self.versions_with_candidate_pairs}**",
            f"- Average skip rate: **{self.avg_skip_rate * 100:.1f}%**",
            f"- Maximum skip rate: **{self.max_skip_rate * 100:.1f}%**",
            f"- High-skip versions (>= 80%): **{self.high_skip_versions}**",
            f"- Total candidate pairs: **{self.total_candidate_pairs}**",
            f"- Total fragments w/o MNN: **{self.total_fragments_no_mnn}**",
            f"- Total fragments with single MNN: **{self.total_fragments_single_mnn}**",
            f"- Total image fragments: **{self.total_fragments_image}**",
            "",
        ]

        if self.top_versions_by_skip_rate:
            lines.extend(
                [
                    "## Top Versions By Skip Rate",
                    "",
                    "| version_id | registry_id | skip_rate | pairs | no_mnn | single_mnn | image |",
                    "|---:|---:|---:|---:|---:|---:|---:|",
                ]
            )
            for item in self.top_versions_by_skip_rate:
                lines.append(
                    "| {version} | {registry} | {skip:.1f}% | {pairs} | {no_mnn} | {single_mnn} | {image} |".format(
                        version=item.document_version_id,
                        registry=item.document_registry_id,
                        skip=item.candidate_skip_rate * 100,
                        pairs=item.candidate_pairs_count,
                        no_mnn=item.candidate_fragments_no_mnn,
                        single_mnn=item.candidate_fragments_single_mnn,
                        image=item.candidate_fragments_image,
                    )
                )
        return "\n".join(lines)


class CandidateDiagnosticsReportService:
    """Build candidate diagnostics report from recent successful extract events."""

    def generate_report(
        self,
        *,
        max_versions: int = 100,
        high_skip_threshold: float = 0.8,
        top_n: int = 10,
    ) -> CandidateDiagnosticsReport:
        session = get_sync_session()
        try:
            events = (
                session.query(PipelineEventLog)
                .filter(PipelineEventLog.stage == "extract")
                .filter(PipelineEventLog.status == "success")
                .order_by(PipelineEventLog.created_at.desc(), PipelineEventLog.id.desc())
                .limit(max_versions)
                .all()
            )

            version_rows: list[CandidateVersionDiagnostic] = []
            for event in events:
                detail = event.detail_json or {}
                if "candidate_skip_rate" not in detail:
                    continue
                if not isinstance(event.document_version_id, int):
                    continue

                version_rows.append(
                    CandidateVersionDiagnostic(
                        event_id=event.id,
                        created_at=str(event.created_at),
                        document_registry_id=_safe_int(event.document_registry_id),
                        document_version_id=event.document_version_id,
                        candidate_pairs_count=_safe_int(detail.get("candidate_pairs_count")),
                        candidate_skip_rate=max(0.0, min(1.0, _safe_float(detail.get("candidate_skip_rate")))),
                        candidate_fragments_no_mnn=_safe_int(detail.get("candidate_fragments_no_mnn")),
                        candidate_fragments_single_mnn=_safe_int(detail.get("candidate_fragments_single_mnn")),
                        candidate_fragments_image=_safe_int(detail.get("candidate_fragments_image")),
                        version_score_contexts_count=_safe_int(detail.get("version_score_contexts_count")),
                    )
                )

            if not version_rows:
                return CandidateDiagnosticsReport()

            skip_rates = [row.candidate_skip_rate for row in version_rows]
            report = CandidateDiagnosticsReport(
                versions_considered=len(version_rows),
                versions_with_candidate_pairs=sum(1 for row in version_rows if row.candidate_pairs_count > 0),
                avg_skip_rate=mean(skip_rates),
                max_skip_rate=max(skip_rates),
                high_skip_versions=sum(1 for row in version_rows if row.candidate_skip_rate >= high_skip_threshold),
                total_candidate_pairs=sum(row.candidate_pairs_count for row in version_rows),
                total_fragments_no_mnn=sum(row.candidate_fragments_no_mnn for row in version_rows),
                total_fragments_single_mnn=sum(row.candidate_fragments_single_mnn for row in version_rows),
                total_fragments_image=sum(row.candidate_fragments_image for row in version_rows),
                top_versions_by_skip_rate=sorted(
                    version_rows,
                    key=lambda row: (row.candidate_skip_rate, row.event_id),
                    reverse=True,
                )[:top_n],
            )
            return report
        finally:
            session.close()
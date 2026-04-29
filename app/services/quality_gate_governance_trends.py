"""Trend analytics for governance score and incident registry signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService
from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService


@dataclass
class GovernanceTrendPoint:
    timestamp: str
    score: float
    escalated_ratio: float
    incidents_total: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "score": round(self.score, 2),
            "escalated_ratio": round(self.escalated_ratio, 4),
            "incidents_total": self.incidents_total,
        }


@dataclass
class GovernanceTrendsReport:
    status: str
    summary: str
    current_score: float
    baseline_score: float
    score_delta: float
    current_escalated_ratio: float
    baseline_escalated_ratio: float
    escalated_ratio_delta: float
    points: list[GovernanceTrendPoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "current_score": round(self.current_score, 2),
            "baseline_score": round(self.baseline_score, 2),
            "score_delta": round(self.score_delta, 2),
            "current_escalated_ratio": round(self.current_escalated_ratio, 4),
            "baseline_escalated_ratio": round(self.baseline_escalated_ratio, 4),
            "escalated_ratio_delta": round(self.escalated_ratio_delta, 4),
            "points": [point.to_dict() for point in self.points],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Governance Trends",
            "",
            f"**Status:** {self.status.upper()}",
            "",
            self.summary,
            "",
            f"- current_score: {self.current_score:.2f}",
            f"- baseline_score: {self.baseline_score:.2f}",
            f"- score_delta: {self.score_delta:.2f}",
            f"- current_escalated_ratio: {self.current_escalated_ratio:.4f}",
            f"- baseline_escalated_ratio: {self.baseline_escalated_ratio:.4f}",
            f"- escalated_ratio_delta: {self.escalated_ratio_delta:.4f}",
            "",
            "## Trend Points",
            "",
            "| timestamp | score | escalated_ratio | incidents_total |",
            "|---|---:|---:|---:|",
        ]
        for point in self.points:
            lines.append(
                f"| {point.timestamp} | {point.score:.2f} | {point.escalated_ratio:.4f} | {point.incidents_total} |"
            )
        if not self.points:
            lines.append("| n/a | 0.00 | 0.0000 | 0 |")
        return "\n".join(lines)


class QualityGateGovernanceTrendsService:
    """Build compact trends report using current score and incident registry history."""

    def __init__(
        self,
        *,
        score_service: QualityGateGovernanceScoreService | None = None,
        registry_service: QualityGateIncidentRegistryService | None = None,
    ):
        self._score = score_service or QualityGateGovernanceScoreService()
        self._registry = registry_service or QualityGateIncidentRegistryService()

    def evaluate(
        self,
        *,
        max_versions: int = 100,
        high_skip_threshold: float = 0.8,
        max_avg_skip_rate: float = 0.75,
        min_candidate_pairs: int = 1,
        spool_dir: str = ".artifacts/quality_gate_notify_queue",
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        max_items: int = 50,
        baseline_window: int = 10,
    ) -> GovernanceTrendsReport:
        baseline_window = max(2, int(baseline_window))
        max_items = max(max_items, baseline_window)

        score_report = self._score.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
        )
        registry_report = self._registry.generate_report(registry_dir=registry_dir, max_items=max_items).to_dict()
        items = registry_report.get("items") if isinstance(registry_report.get("items"), list) else []

        points = self._build_points(items, score_report.score, baseline_window)
        baseline = points[0] if points else GovernanceTrendPoint(timestamp="baseline", score=score_report.score, escalated_ratio=0.0, incidents_total=0)
        current = points[-1] if points else GovernanceTrendPoint(timestamp=datetime.now(timezone.utc).isoformat(), score=score_report.score, escalated_ratio=0.0, incidents_total=0)

        score_delta = current.score - baseline.score
        ratio_delta = current.escalated_ratio - baseline.escalated_ratio

        if score_delta >= 5 and ratio_delta <= 0:
            status = "improving"
            summary = "Governance trend is improving versus baseline window."
        elif score_delta <= -5 or ratio_delta >= 0.2:
            status = "degrading"
            summary = "Governance trend is degrading and requires operational attention."
        else:
            status = "stable"
            summary = "Governance trend is stable with no major drift."

        return GovernanceTrendsReport(
            status=status,
            summary=summary,
            current_score=current.score,
            baseline_score=baseline.score,
            score_delta=score_delta,
            current_escalated_ratio=current.escalated_ratio,
            baseline_escalated_ratio=baseline.escalated_ratio,
            escalated_ratio_delta=ratio_delta,
            points=points,
        )

    @staticmethod
    def _build_points(items: list[dict[str, Any]], current_score: float, baseline_window: int) -> list[GovernanceTrendPoint]:
        if not items:
            now = datetime.now(timezone.utc).isoformat()
            return [GovernanceTrendPoint(timestamp=now, score=current_score, escalated_ratio=0.0, incidents_total=0)]

        total = len(items)
        escalated = 0
        points: list[GovernanceTrendPoint] = []

        start_idx = max(0, total - baseline_window)
        subset = items[start_idx:]
        for idx, item in enumerate(subset, start=1):
            if item.get("should_escalate"):
                escalated += 1
            ratio = escalated / idx if idx else 0.0
            dampener = min(20.0, ratio * 25.0)
            point_score = max(0.0, min(100.0, current_score - dampener))
            points.append(
                GovernanceTrendPoint(
                    timestamp=str(item.get("created_at") or f"point-{idx}"),
                    score=point_score,
                    escalated_ratio=ratio,
                    incidents_total=idx,
                )
            )
        return points

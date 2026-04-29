"""Adaptive policy recommendation service based on governance trends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService
from app.services.quality_gate_governance_trends import QualityGateGovernanceTrendsService


@dataclass
class AdaptivePolicyRecommendation:
    key: str
    current_value: float
    recommended_value: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "current_value": round(self.current_value, 4),
            "recommended_value": round(self.recommended_value, 4),
            "reason": self.reason,
        }


@dataclass
class AdaptivePolicyReport:
    mode: str
    summary: str
    score: float
    trend_status: str
    recommendations: list[AdaptivePolicyRecommendation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "summary": self.summary,
            "score": round(self.score, 2),
            "trend_status": self.trend_status,
            "recommendations": [rec.to_dict() for rec in self.recommendations],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Adaptive Policy",
            "",
            f"- mode: {self.mode}",
            f"- score: {self.score:.2f}",
            f"- trend_status: {self.trend_status}",
            "",
            self.summary,
            "",
            "## Recommendations",
            "",
            "| key | current | recommended | reason |",
            "|---|---:|---:|---|",
        ]
        if self.recommendations:
            for rec in self.recommendations:
                lines.append(
                    f"| {rec.key} | {rec.current_value:.4f} | {rec.recommended_value:.4f} | {rec.reason} |"
                )
        else:
            lines.append("| n/a | 0 | 0 | no changes |")
        return "\n".join(lines)


class QualityGateAdaptivePolicyService:
    """Recommend threshold tuning from score + trends state."""

    def __init__(
        self,
        *,
        score_service: QualityGateGovernanceScoreService | None = None,
        trends_service: QualityGateGovernanceTrendsService | None = None,
    ):
        self._score = score_service or QualityGateGovernanceScoreService()
        self._trends = trends_service or QualityGateGovernanceTrendsService()

    def recommend(
        self,
        *,
        max_versions: int = 100,
        high_skip_threshold: float = 0.8,
        max_avg_skip_rate: float = 0.75,
        min_candidate_pairs: int = 1,
        queue_size_warn: float = 20.0,
        queue_size_fail: float = 100.0,
        baseline_window: int = 10,
        spool_dir: str = ".artifacts/quality_gate_notify_queue",
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        max_items: int = 50,
    ) -> AdaptivePolicyReport:
        score = self._score.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
        )
        trends = self._trends.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
            baseline_window=baseline_window,
        )

        recs: list[AdaptivePolicyRecommendation] = []

        if trends.status == "degrading" or score.score < 60:
            mode = "tighten"
            recs.append(
                AdaptivePolicyRecommendation(
                    key="high_skip_threshold",
                    current_value=high_skip_threshold,
                    recommended_value=max(0.5, high_skip_threshold - 0.05),
                    reason="Degrading trend requires stricter high-skip guardrail.",
                )
            )
            recs.append(
                AdaptivePolicyRecommendation(
                    key="max_avg_skip_rate",
                    current_value=max_avg_skip_rate,
                    recommended_value=max(0.5, max_avg_skip_rate - 0.05),
                    reason="Lower average skip limit under elevated risk.",
                )
            )
            recs.append(
                AdaptivePolicyRecommendation(
                    key="queue_size_warn",
                    current_value=queue_size_warn,
                    recommended_value=max(5.0, queue_size_warn - 3.0),
                    reason="Warn sooner on queue growth during degradation.",
                )
            )
            recs.append(
                AdaptivePolicyRecommendation(
                    key="queue_size_fail",
                    current_value=queue_size_fail,
                    recommended_value=max(20.0, queue_size_fail - 10.0),
                    reason="Fail earlier on sustained backlog risk.",
                )
            )
            summary = "Policy tightening recommended due to degrading trend or low governance score."
        elif trends.status == "improving" and score.score >= 85:
            mode = "relax"
            recs.append(
                AdaptivePolicyRecommendation(
                    key="high_skip_threshold",
                    current_value=high_skip_threshold,
                    recommended_value=min(0.95, high_skip_threshold + 0.03),
                    reason="Stable improving trend allows moderate relaxation.",
                )
            )
            recs.append(
                AdaptivePolicyRecommendation(
                    key="max_avg_skip_rate",
                    current_value=max_avg_skip_rate,
                    recommended_value=min(0.9, max_avg_skip_rate + 0.03),
                    reason="Increase tolerance under consistently healthy governance.",
                )
            )
            recs.append(
                AdaptivePolicyRecommendation(
                    key="queue_size_warn",
                    current_value=queue_size_warn,
                    recommended_value=min(100.0, queue_size_warn + 2.0),
                    reason="Relax queue warning threshold when recovery is observed.",
                )
            )
            summary = "Policy relaxation recommended due to improving trend and high score."
        else:
            mode = "hold"
            summary = "Current policy is balanced; keep thresholds unchanged."

        return AdaptivePolicyReport(
            mode=mode,
            summary=summary,
            score=score.score,
            trend_status=trends.status,
            recommendations=recs,
        )

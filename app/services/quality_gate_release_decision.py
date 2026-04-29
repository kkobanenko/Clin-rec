"""Release decision engine based on governance signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.quality_gate_adaptive_policy import QualityGateAdaptivePolicyService
from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService
from app.services.quality_gate_governance_trends import QualityGateGovernanceTrendsService


@dataclass
class ReleaseDecisionRule:
    name: str
    status: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
        }


@dataclass
class ReleaseDecisionReport:
    decision: str
    confidence: float
    summary: str
    rules: list[ReleaseDecisionRule] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "confidence": round(self.confidence, 2),
            "summary": self.summary,
            "rules": [rule.to_dict() for rule in self.rules],
            "context": self.context,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Release Decision",
            "",
            f"**Decision:** {self.decision.upper()}",
            f"**Confidence:** {self.confidence:.2f}",
            "",
            self.summary,
            "",
            "## Rules",
            "",
            "| name | status | message |",
            "|---|---|---|",
        ]
        for rule in self.rules:
            lines.append(f"| {rule.name} | {rule.status} | {rule.message} |")
        if not self.rules:
            lines.append("| n/a | n/a | no rules evaluated |")
        return "\n".join(lines)


class QualityGateReleaseDecisionService:
    """Compute final release decision from governance evidence."""

    def __init__(
        self,
        *,
        score_service: QualityGateGovernanceScoreService | None = None,
        trends_service: QualityGateGovernanceTrendsService | None = None,
        adaptive_service: QualityGateAdaptivePolicyService | None = None,
    ):
        self._score = score_service or QualityGateGovernanceScoreService()
        self._trends = trends_service or QualityGateGovernanceTrendsService()
        self._adaptive = adaptive_service or QualityGateAdaptivePolicyService()

    def evaluate(
        self,
        *,
        min_score: float = 60.0,
        max_allowed_ratio_delta: float = 0.15,
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
    ) -> ReleaseDecisionReport:
        score_report = self._score.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
        )
        trends_report = self._trends.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
            baseline_window=baseline_window,
        )
        adaptive_report = self._adaptive.recommend(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            queue_size_warn=queue_size_warn,
            queue_size_fail=queue_size_fail,
            baseline_window=baseline_window,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
        )

        rules: list[ReleaseDecisionRule] = []

        score_ok = score_report.score >= min_score
        rules.append(
            ReleaseDecisionRule(
                name="min_score",
                status="pass" if score_ok else "fail",
                message=f"score={score_report.score:.2f} min_required={min_score:.2f}",
            )
        )

        trend_ok = trends_report.status != "degrading" and trends_report.escalated_ratio_delta <= max_allowed_ratio_delta
        rules.append(
            ReleaseDecisionRule(
                name="trend_stability",
                status="pass" if trend_ok else "fail",
                message=(
                    f"status={trends_report.status} ratio_delta={trends_report.escalated_ratio_delta:.4f} "
                    f"max_allowed={max_allowed_ratio_delta:.4f}"
                ),
            )
        )

        adaptive_ok = adaptive_report.mode != "tighten"
        rules.append(
            ReleaseDecisionRule(
                name="adaptive_mode",
                status="pass" if adaptive_ok else "warn",
                message=f"adaptive_mode={adaptive_report.mode}",
            )
        )

        failed_rules = [rule for rule in rules if rule.status == "fail"]
        warning_rules = [rule for rule in rules if rule.status == "warn"]

        if failed_rules:
            decision = "block"
            confidence = 0.9
            summary = "Release should be blocked: critical governance constraints are violated."
        elif warning_rules:
            decision = "review"
            confidence = 0.7
            summary = "Release requires manual review due to adaptive tightening signal."
        else:
            decision = "allow"
            confidence = 0.95
            summary = "Release can proceed based on current governance evidence."

        context = {
            "score": score_report.score,
            "score_status": score_report.status,
            "trend_status": trends_report.status,
            "trend_score_delta": trends_report.score_delta,
            "trend_ratio_delta": trends_report.escalated_ratio_delta,
            "adaptive_mode": adaptive_report.mode,
        }

        return ReleaseDecisionReport(
            decision=decision,
            confidence=confidence,
            summary=summary,
            rules=rules,
            context=context,
        )

"""Automated quality gate service for release readiness.

Combines corpus quality and candidate diagnostics into a single verdict that
can be consumed by operators and release checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.candidate_diagnostics_report import CandidateDiagnosticsReportService
from app.services.corpus_quality import CorpusQualityService


@dataclass
class QualityGateRuleResult:
    """One evaluated quality gate rule."""

    name: str
    status: str  # pass | warn | fail
    value: float
    threshold: float
    comparator: str  # <= | >=
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "value": round(self.value, 4),
            "threshold": round(self.threshold, 4),
            "comparator": self.comparator,
            "message": self.message,
        }


@dataclass
class QualityGateReport:
    """Top-level quality gate output."""

    verdict: str = "unknown"  # pass | warn | fail | no-data
    summary: str = ""
    rules: list[QualityGateRuleResult] = field(default_factory=list)
    corpus_quality: dict[str, Any] = field(default_factory=dict)
    candidate_diagnostics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "summary": self.summary,
            "rules": [rule.to_dict() for rule in self.rules],
            "corpus_quality": self.corpus_quality,
            "candidate_diagnostics": self.candidate_diagnostics,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Automated Quality Gate",
            "",
            f"**Verdict:** {self.verdict.upper()}",
            "",
            self.summary,
            "",
            "## Rules",
            "",
            "| Rule | Status | Value | Comparator | Threshold |",
            "|---|---|---:|:---:|---:|",
        ]
        for rule in self.rules:
            lines.append(
                f"| {rule.name} | {rule.status} | {rule.value:.4f} | {rule.comparator} | {rule.threshold:.4f} |"
            )

        cq_health = self.corpus_quality.get("overall_health", "unknown")
        cd_avg_skip = self.candidate_diagnostics.get("avg_skip_rate", 0.0)
        lines.extend(
            [
                "",
                "## Snapshot",
                "",
                f"- corpus_quality.overall_health: **{cq_health}**",
                f"- candidate_diagnostics.avg_skip_rate: **{float(cd_avg_skip) * 100:.1f}%**",
            ]
        )
        return "\n".join(lines)


class QualityGateService:
    """Evaluate automated quality gate rules for release readiness."""

    def __init__(
        self,
        *,
        corpus_quality_service: CorpusQualityService | None = None,
        candidate_diagnostics_service: CandidateDiagnosticsReportService | None = None,
    ):
        self._cq = corpus_quality_service or CorpusQualityService()
        self._cd = candidate_diagnostics_service or CandidateDiagnosticsReportService()

    def evaluate(
        self,
        *,
        max_versions: int = 100,
        high_skip_threshold: float = 0.8,
        max_avg_skip_rate: float = 0.75,
        min_candidate_pairs: int = 1,
    ) -> QualityGateReport:
        """Return release gate verdict and rule-by-rule diagnostics."""
        cq_report = self._cq.generate_report().to_dict()
        cd_report = self._cd.generate_report(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
        ).to_dict()

        rules: list[QualityGateRuleResult] = []
        fail_count = 0
        warn_count = 0

        cq_health = str(cq_report.get("overall_health") or "unknown")
        health_value = 0.0 if cq_health in {"healthy", "degraded"} else 1.0
        health_status = "pass" if cq_health in {"healthy", "degraded"} else "fail"
        if health_status == "fail":
            fail_count += 1
        rules.append(
            QualityGateRuleResult(
                name="corpus_health_allowed",
                status=health_status,
                value=health_value,
                threshold=0.0,
                comparator="<=",
                message=(
                    f"corpus overall health is {cq_health}; allowed states: healthy/degraded"
                ),
            )
        )

        avg_skip_rate = float(cd_report.get("avg_skip_rate") or 0.0)
        skip_status = "pass" if avg_skip_rate <= max_avg_skip_rate else "warn"
        if skip_status == "warn":
            warn_count += 1
        rules.append(
            QualityGateRuleResult(
                name="avg_skip_rate",
                status=skip_status,
                value=avg_skip_rate,
                threshold=max_avg_skip_rate,
                comparator="<=",
                message=(
                    f"average candidate skip rate {avg_skip_rate * 100:.1f}%"
                ),
            )
        )

        total_pairs = float(cd_report.get("total_candidate_pairs") or 0.0)
        pairs_status = "pass" if total_pairs >= float(min_candidate_pairs) else "fail"
        if pairs_status == "fail":
            fail_count += 1
        rules.append(
            QualityGateRuleResult(
                name="candidate_pairs_total",
                status=pairs_status,
                value=total_pairs,
                threshold=float(min_candidate_pairs),
                comparator=">=",
                message=f"total candidate pairs across window: {int(total_pairs)}",
            )
        )

        high_skip_versions = float(cd_report.get("high_skip_versions") or 0.0)
        versions_considered = float(cd_report.get("versions_considered") or 0.0)
        high_skip_fraction = high_skip_versions / versions_considered if versions_considered > 0 else 1.0
        burst_status = "pass" if high_skip_fraction <= 0.5 else "warn"
        if burst_status == "warn":
            warn_count += 1
        rules.append(
            QualityGateRuleResult(
                name="high_skip_fraction",
                status=burst_status,
                value=high_skip_fraction,
                threshold=0.5,
                comparator="<=",
                message=(
                    f"high-skip versions fraction {high_skip_fraction * 100:.1f}% "
                    f"({int(high_skip_versions)}/{int(versions_considered)})"
                ),
            )
        )

        if int(versions_considered) == 0:
            verdict = "no-data"
            summary = "No candidate diagnostics data in selected window; run extract pipeline first."
        elif fail_count > 0:
            verdict = "fail"
            summary = f"Quality gate failed: {fail_count} fail rule(s), {warn_count} warning rule(s)."
        elif warn_count > 0:
            verdict = "warn"
            summary = f"Quality gate warning: {warn_count} warning rule(s), no hard failures."
        else:
            verdict = "pass"
            summary = "Quality gate passed: all rules are within configured thresholds."

        return QualityGateReport(
            verdict=verdict,
            summary=summary,
            rules=rules,
            corpus_quality=cq_report,
            candidate_diagnostics=cd_report,
        )
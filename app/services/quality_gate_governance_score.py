"""Aggregate governance score from quality gate, queue policy, incident, and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.quality_gate import QualityGateService
from app.services.quality_gate_incident import QualityGateIncidentService
from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService
from app.services.quality_gate_queue_policy import QualityGateQueuePolicyService


@dataclass
class GovernanceComponent:
    name: str
    score: float
    weight: float
    verdict: str
    detail: str

    def weighted_score(self) -> float:
        return self.score * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "weight": round(self.weight, 2),
            "weighted_score": round(self.weighted_score(), 2),
            "verdict": self.verdict,
            "detail": self.detail,
        }


@dataclass
class GovernanceScoreReport:
    score: float
    status: str
    summary: str
    components: list[GovernanceComponent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "status": self.status,
            "summary": self.summary,
            "components": [component.to_dict() for component in self.components],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Governance Score",
            "",
            f"**Score:** {self.score:.2f}",
            f"**Status:** {self.status.upper()}",
            "",
            self.summary,
            "",
            "## Components",
            "",
            "| Component | Verdict | Score | Weight | Weighted |",
            "|---|---|---:|---:|---:|",
        ]

        for component in self.components:
            lines.append(
                "| {name} | {verdict} | {score:.2f} | {weight:.2f} | {weighted:.2f} |".format(
                    name=component.name,
                    verdict=component.verdict,
                    score=component.score,
                    weight=component.weight,
                    weighted=component.weighted_score(),
                )
            )

        return "\n".join(lines)


class QualityGateGovernanceScoreService:
    """Compute weighted governance score for release readiness."""

    def __init__(
        self,
        *,
        gate_service: QualityGateService | None = None,
        queue_policy_service: QualityGateQueuePolicyService | None = None,
        incident_service: QualityGateIncidentService | None = None,
        registry_service: QualityGateIncidentRegistryService | None = None,
    ):
        self._gate = gate_service or QualityGateService()
        self._queue_policy = queue_policy_service or QualityGateQueuePolicyService()
        self._incident = incident_service or QualityGateIncidentService()
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
    ) -> GovernanceScoreReport:
        gate_payload = self._gate.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
        ).to_dict()
        queue_payload = self._queue_policy.evaluate(spool_dir=spool_dir, max_items=max_items).to_dict()
        incident_payload = self._incident.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            max_items=max_items,
        ).to_dict()
        registry_payload = self._registry.generate_report(registry_dir=registry_dir, max_items=max_items).to_dict()

        components = [
            self._score_gate(gate_payload),
            self._score_queue_policy(queue_payload),
            self._score_incident(incident_payload),
            self._score_registry(registry_payload),
        ]

        total_weight = sum(item.weight for item in components) or 1.0
        weighted_sum = sum(item.weighted_score() for item in components)
        total_score = weighted_sum / total_weight

        if total_score >= 85:
            status = "good"
            summary = "Governance score indicates stable release conditions."
        elif total_score >= 60:
            status = "warning"
            summary = "Governance score indicates elevated operational risk."
        else:
            status = "critical"
            summary = "Governance score indicates high risk; release should be blocked."

        return GovernanceScoreReport(
            score=total_score,
            status=status,
            summary=summary,
            components=components,
        )

    @staticmethod
    def _score_gate(payload: dict[str, Any]) -> GovernanceComponent:
        verdict = str(payload.get("verdict") or "unknown")
        mapping = {"pass": 100.0, "warn": 65.0, "fail": 20.0, "no-data": 45.0, "unknown": 10.0}
        score = mapping.get(verdict, 10.0)
        return GovernanceComponent(
            name="quality_gate",
            score=score,
            weight=0.35,
            verdict=verdict,
            detail=str(payload.get("summary") or ""),
        )

    @staticmethod
    def _score_queue_policy(payload: dict[str, Any]) -> GovernanceComponent:
        verdict = str(payload.get("verdict") or "unknown")
        mapping = {"healthy": 100.0, "degraded": 60.0, "critical": 20.0, "empty": 85.0, "unknown": 15.0}
        score = mapping.get(verdict, 15.0)
        return GovernanceComponent(
            name="queue_policy",
            score=score,
            weight=0.25,
            verdict=verdict,
            detail=str(payload.get("summary") or ""),
        )

    @staticmethod
    def _score_incident(payload: dict[str, Any]) -> GovernanceComponent:
        severity = str(payload.get("severity") or "info")
        should_escalate = bool(payload.get("should_escalate"))
        if severity == "critical":
            score = 10.0
        elif severity == "high":
            score = 50.0
        else:
            score = 95.0 if not should_escalate else 70.0
        return GovernanceComponent(
            name="incident",
            score=score,
            weight=0.25,
            verdict=severity,
            detail=str(payload.get("reason") or ""),
        )

    @staticmethod
    def _score_registry(payload: dict[str, Any]) -> GovernanceComponent:
        total = int(payload.get("total_items") or 0)
        escalated = int(payload.get("escalate_items") or 0)
        if total <= 0:
            score = 90.0
            verdict = "empty"
            detail = "No incident history recorded yet"
        else:
            ratio = escalated / total if total > 0 else 0.0
            if ratio >= 0.7:
                score = 30.0
                verdict = "critical"
            elif ratio >= 0.4:
                score = 55.0
                verdict = "warning"
            else:
                score = 85.0
                verdict = "healthy"
            detail = f"escalated_ratio={ratio:.2f} ({escalated}/{total})"

        return GovernanceComponent(
            name="incident_registry",
            score=score,
            weight=0.15,
            verdict=verdict,
            detail=detail,
        )

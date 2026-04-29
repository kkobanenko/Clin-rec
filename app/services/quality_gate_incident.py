"""Incident escalation report derived from quality gate and queue policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.quality_gate import QualityGateService
from app.services.quality_gate_queue_policy import QualityGateQueuePolicyService


@dataclass
class IncidentReport:
    should_escalate: bool
    severity: str
    reason: str
    actions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_escalate": self.should_escalate,
            "severity": self.severity,
            "reason": self.reason,
            "actions": self.actions,
            "tags": self.tags,
            "details": self.details,
            "created_at": self.created_at,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Incident Escalation",
            "",
            f"**Escalate:** {'YES' if self.should_escalate else 'NO'}",
            f"**Severity:** {self.severity.upper()}",
            "",
            self.reason,
            "",
            "## Actions",
            "",
        ]
        if self.actions:
            lines.extend([f"- {item}" for item in self.actions])
        else:
            lines.append("- No immediate action required")

        lines.extend(["", "## Tags", ""])
        if self.tags:
            lines.extend([f"- {item}" for item in self.tags])
        else:
            lines.append("- none")

        lines.extend(["", "## Details", ""])
        details = self.details or {}
        for key in sorted(details):
            lines.append(f"- {key}: {details[key]}")
        if not details:
            lines.append("- none")

        return "\n".join(lines)


class QualityGateIncidentService:
    """Build incident escalation report from gate and queue policy signals."""

    def __init__(
        self,
        *,
        gate_service: QualityGateService | None = None,
        queue_policy_service: QualityGateQueuePolicyService | None = None,
    ):
        self._gate = gate_service or QualityGateService()
        self._queue_policy = queue_policy_service or QualityGateQueuePolicyService()

    def evaluate(
        self,
        *,
        max_versions: int = 100,
        high_skip_threshold: float = 0.8,
        max_avg_skip_rate: float = 0.75,
        min_candidate_pairs: int = 1,
        spool_dir: str = ".artifacts/quality_gate_notify_queue",
        max_items: int = 50,
    ) -> IncidentReport:
        gate = self._gate.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
        ).to_dict()
        queue_policy = self._queue_policy.evaluate(
            spool_dir=spool_dir,
            max_items=max_items,
        ).to_dict()

        gate_verdict = str(gate.get("verdict") or "unknown")
        queue_verdict = str(queue_policy.get("verdict") or "unknown")

        reason_parts: list[str] = []
        tags: list[str] = []
        actions: list[str] = []
        severity = "info"
        should_escalate = False

        if gate_verdict in {"fail", "unknown"}:
            should_escalate = True
            severity = "critical"
            reason_parts.append(f"Quality gate verdict is {gate_verdict}")
            tags.extend(["quality-gate", "release-blocking"])
            actions.extend(
                [
                    "Stop release workflow and inspect failing gate rules.",
                    "Review latest outputs and candidate diagnostics before retry.",
                ]
            )
        elif gate_verdict == "warn":
            should_escalate = True
            severity = "high"
            reason_parts.append("Quality gate is in warning state")
            tags.extend(["quality-gate", "warning-state"])
            actions.append("Review warning-level gate rules and decide if promotion is allowed.")

        if queue_verdict == "critical":
            should_escalate = True
            severity = "critical"
            reason_parts.append("Queue policy is critical")
            tags.extend(["queue-policy", "delivery-backlog"])
            actions.extend(
                [
                    "Run queue drain in strict mode and verify webhook availability.",
                    "Reduce event generation rate until backlog recovers.",
                ]
            )
        elif queue_verdict == "degraded":
            should_escalate = True
            if severity != "critical":
                severity = "high"
            reason_parts.append("Queue policy is degraded")
            tags.extend(["queue-policy", "backlog-risk"])
            actions.append("Run queue drain in best-effort mode and monitor queue age trend.")

        if not should_escalate:
            reason_parts.append("Gate and queue policy are within acceptable boundaries")
            actions.append("Continue routine release monitoring.")
            tags.extend(["quality-gate", "healthy"])

        details = {
            "gate_verdict": gate_verdict,
            "queue_policy_verdict": queue_verdict,
            "gate_summary": str(gate.get("summary") or ""),
            "queue_policy_summary": str(queue_policy.get("summary") or ""),
            "queue_size": (queue_policy.get("queue_status") or {}).get("queue_size"),
            "queue_oldest_age_seconds": (queue_policy.get("queue_status") or {}).get("oldest_age_seconds"),
        }

        return IncidentReport(
            should_escalate=should_escalate,
            severity=severity,
            reason="; ".join(reason_parts),
            actions=_deduplicate(actions),
            tags=_deduplicate(tags),
            details=details,
        )


def _deduplicate(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

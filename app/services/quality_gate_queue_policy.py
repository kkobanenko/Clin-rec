"""Policy/SLO evaluation for quality gate notification queue."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.quality_gate_queue_status import QualityGateQueueStatusService

_DEFAULT_POLICY: dict[str, float] = {
    "queue_size_warn": 20,
    "queue_size_fail": 100,
    "oldest_age_warn": 900,   # 15 minutes
    "oldest_age_fail": 3600,  # 1 hour
    "total_size_warn": 1_000_000,
    "total_size_fail": 10_000_000,
}


@dataclass
class QueuePolicyRuleResult:
    name: str
    status: str  # pass | warn | fail
    value: float
    warn_threshold: float
    fail_threshold: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "value": round(self.value, 2),
            "warn_threshold": round(self.warn_threshold, 2),
            "fail_threshold": round(self.fail_threshold, 2),
            "message": self.message,
        }


@dataclass
class QueuePolicyReport:
    verdict: str = "unknown"  # healthy | degraded | critical | empty | unknown
    summary: str = ""
    actions: list[str] = field(default_factory=list)
    rules: list[QueuePolicyRuleResult] = field(default_factory=list)
    queue_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "summary": self.summary,
            "actions": self.actions,
            "rules": [rule.to_dict() for rule in self.rules],
            "queue_status": self.queue_status,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Queue Policy",
            "",
            f"**Verdict:** {self.verdict.upper()}",
            "",
            self.summary,
            "",
            "## Rules",
            "",
            "| Rule | Status | Value | Warn | Fail |",
            "|---|---|---:|---:|---:|",
        ]
        for rule in self.rules:
            lines.append(
                "| {name} | {status} | {value:.2f} | {warn:.2f} | {fail:.2f} |".format(
                    name=rule.name,
                    status=rule.status,
                    value=rule.value,
                    warn=rule.warn_threshold,
                    fail=rule.fail_threshold,
                )
            )

        lines.extend(["", "## Recommended Actions", ""])
        if self.actions:
            for action in self.actions:
                lines.append(f"- {action}")
        else:
            lines.append("- No action required")

        return "\n".join(lines)


class QualityGateQueuePolicyService:
    """Evaluate queue backlog against policy thresholds."""

    def __init__(
        self,
        *,
        queue_status_service: QualityGateQueueStatusService | None = None,
        thresholds: dict[str, float] | None = None,
    ):
        self._status = queue_status_service or QualityGateQueueStatusService()
        self._thresholds = {**_DEFAULT_POLICY, **(thresholds or {})}

    def evaluate(
        self,
        *,
        spool_dir: str = ".artifacts/quality_gate_notify_queue",
        max_items: int = 50,
    ) -> QueuePolicyReport:
        status_report = self._status.generate_report(spool_dir=spool_dir, max_items=max_items)
        payload = status_report.to_dict()

        queue_size = float(payload.get("queue_size") or 0.0)
        oldest_age = float(payload.get("oldest_age_seconds") or 0.0)
        total_size = float(payload.get("total_size_bytes") or 0.0)

        if queue_size <= 0:
            return QueuePolicyReport(
                verdict="empty",
                summary="Notification queue is empty.",
                actions=["No queue backlog actions required."],
                rules=[],
                queue_status=payload,
            )

        rules = [
            self._evaluate_rule(
                name="queue_size",
                value=queue_size,
                warn_threshold=self._thresholds["queue_size_warn"],
                fail_threshold=self._thresholds["queue_size_fail"],
                unit="items",
            ),
            self._evaluate_rule(
                name="oldest_age_seconds",
                value=oldest_age,
                warn_threshold=self._thresholds["oldest_age_warn"],
                fail_threshold=self._thresholds["oldest_age_fail"],
                unit="seconds",
            ),
            self._evaluate_rule(
                name="total_size_bytes",
                value=total_size,
                warn_threshold=self._thresholds["total_size_warn"],
                fail_threshold=self._thresholds["total_size_fail"],
                unit="bytes",
            ),
        ]

        fail_count = sum(1 for rule in rules if rule.status == "fail")
        warn_count = sum(1 for rule in rules if rule.status == "warn")

        if fail_count > 0:
            verdict = "critical"
            summary = f"Queue policy failed: {fail_count} fail rule(s), {warn_count} warning rule(s)."
            actions = [
                "Run queue drain immediately and verify webhook reachability.",
                "Switch notifier to required mode until backlog stabilizes.",
            ]
        elif warn_count > 0:
            verdict = "degraded"
            summary = f"Queue policy warning: {warn_count} warning rule(s), no hard failures."
            actions = [
                "Run queue drain in best-effort mode and monitor age trend.",
                "Inspect webhook latency and downstream endpoint health.",
            ]
        else:
            verdict = "healthy"
            summary = "Queue policy healthy: all queue SLO rules are within thresholds."
            actions = ["No urgent action required. Continue routine monitoring."]

        return QueuePolicyReport(
            verdict=verdict,
            summary=summary,
            actions=actions,
            rules=rules,
            queue_status=payload,
        )

    @staticmethod
    def _evaluate_rule(
        *,
        name: str,
        value: float,
        warn_threshold: float,
        fail_threshold: float,
        unit: str,
    ) -> QueuePolicyRuleResult:
        if value >= fail_threshold:
            status = "fail"
        elif value >= warn_threshold:
            status = "warn"
        else:
            status = "pass"
        message = (
            f"{name}={value:.2f} {unit}; warn>={warn_threshold:.2f}, fail>={fail_threshold:.2f}"
        )
        return QueuePolicyRuleResult(
            name=name,
            status=status,
            value=value,
            warn_threshold=warn_threshold,
            fail_threshold=fail_threshold,
            message=message,
        )

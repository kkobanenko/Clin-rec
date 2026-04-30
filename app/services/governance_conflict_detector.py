"""Detect conflicts across governance verdicts."""

from __future__ import annotations


class GovernanceConflictDetectorService:
    """Find incompatible combinations in governance outcomes."""

    def detect(self, payload: dict) -> dict:
        score_status = str(payload.get("score_status") or "unknown")
        trend_status = str(payload.get("trend_status") or "unknown")
        adaptive_mode = str(payload.get("adaptive_mode") or "unknown")
        decision = str(payload.get("decision") or "unknown")

        conflicts: list[str] = []

        if score_status == "critical" and decision == "allow":
            conflicts.append("Decision allow conflicts with critical score status")
        if trend_status == "degrading" and decision == "allow":
            conflicts.append("Decision allow conflicts with degrading trend")
        if adaptive_mode == "tighten" and decision == "allow":
            conflicts.append("Decision allow conflicts with tighten recommendation")
        if score_status == "good" and decision == "block":
            conflicts.append("Decision block conflicts with good score status")

        severity = "none"
        if conflicts:
            severity = "high" if len(conflicts) >= 2 else "medium"

        return {
            "severity": severity,
            "conflicts": conflicts,
            "count": len(conflicts),
        }

    def to_markdown(self, payload: dict) -> str:
        report = self.detect(payload)
        lines = [
            "# Governance Conflict Detector",
            "",
            f"- severity: {report['severity']}",
            f"- count: {report['count']}",
            "",
            "## Conflicts",
            "",
        ]
        if report["conflicts"]:
            for item in report["conflicts"]:
                lines.append(f"- {item}")
        else:
            lines.append("- none")
        return "\n".join(lines)

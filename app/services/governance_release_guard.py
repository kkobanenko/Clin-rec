"""Final release guard based on composite governance checks."""

from __future__ import annotations


class GovernanceReleaseGuardService:
    def evaluate(self, payload: dict) -> dict:
        score = float(payload.get("normalized_score") or 0.0)
        conflict_count = int(payload.get("conflict_count") or 0)
        drift_severity = str(payload.get("drift_severity") or "low")
        incident_open = bool(payload.get("incident_open") or False)

        reasons: list[str] = []

        if score < 60:
            reasons.append("normalized_score below 60")
        if conflict_count > 0:
            reasons.append("conflicts detected")
        if drift_severity in {"high"}:
            reasons.append("high drift severity")
        if incident_open:
            reasons.append("open governance incident")

        decision = "block" if reasons else "allow"
        confidence = max(0.0, min(1.0, score / 100.0))

        return {
            "decision": decision,
            "confidence": round(confidence, 4),
            "reasons": reasons,
            "inputs": {
                "normalized_score": score,
                "conflict_count": conflict_count,
                "drift_severity": drift_severity,
                "incident_open": incident_open,
            },
        }

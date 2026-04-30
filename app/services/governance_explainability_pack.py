"""Assemble explainability narrative for governance decisions."""

from __future__ import annotations


class GovernanceExplainabilityPackService:
    def build(self, payload: dict) -> dict:
        decision = str(payload.get("decision") or "unknown")
        score = float(payload.get("score") or 0.0)
        reasons = payload.get("reasons") if isinstance(payload.get("reasons"), list) else []
        conflicts = int(payload.get("conflicts") or 0)

        rationale_lines = [
            f"Decision: {decision}",
            f"Score: {score:.2f}",
            f"Conflicts: {conflicts}",
        ]

        if reasons:
            rationale_lines.append("Reasons:")
            for reason in reasons:
                rationale_lines.append(f"- {reason}")
        else:
            rationale_lines.append("Reasons: none provided")

        confidence = max(0.0, min(1.0, score / 100.0))
        if decision == "block":
            confidence = min(confidence, 0.85)

        return {
            "decision": decision,
            "confidence": round(confidence, 4),
            "rationale": "\n".join(rationale_lines),
            "risk_label": "high" if decision == "block" else "managed",
        }

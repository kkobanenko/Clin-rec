"""Compute readiness window for release execution."""

from __future__ import annotations


class GovernanceReadinessWindowService:
    def calculate(self, payload: dict) -> dict:
        score = float(payload.get("score") or 0.0)
        incident_open = bool(payload.get("incident_open") or False)
        degradation = bool(payload.get("degradation") or False)

        if incident_open:
            return {"window": "closed", "minutes": 0, "reason": "incident open"}
        if degradation:
            return {"window": "narrow", "minutes": 30, "reason": "degradation detected"}
        if score >= 85:
            return {"window": "wide", "minutes": 180, "reason": "strong governance score"}
        if score >= 65:
            return {"window": "moderate", "minutes": 90, "reason": "acceptable score"}
        return {"window": "narrow", "minutes": 30, "reason": "low score"}

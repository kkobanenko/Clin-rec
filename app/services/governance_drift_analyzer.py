"""Analyze governance drift between snapshots."""

from __future__ import annotations


class GovernanceDriftAnalyzerService:
    def analyze(self, baseline: dict, current: dict) -> dict:
        keys = sorted(set(baseline.keys()) | set(current.keys()))
        deltas = []
        abs_sum = 0.0
        for key in keys:
            b = float(baseline.get(key) or 0.0)
            c = float(current.get(key) or 0.0)
            delta = c - b
            abs_sum += abs(delta)
            deltas.append({"metric": key, "baseline": b, "current": c, "delta": delta})

        severity = "low"
        if abs_sum >= 50:
            severity = "high"
        elif abs_sum >= 20:
            severity = "medium"

        return {
            "severity": severity,
            "absolute_delta_sum": round(abs_sum, 4),
            "metrics": deltas,
        }

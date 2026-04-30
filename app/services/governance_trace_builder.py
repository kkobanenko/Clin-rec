"""Build normalized governance trace timeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GovernanceTracePoint:
    ts: str
    stage: str
    score: float
    decision: str

    def to_dict(self) -> dict:
        return {
            "ts": self.ts,
            "stage": self.stage,
            "score": round(self.score, 2),
            "decision": self.decision,
        }


class GovernanceTraceBuilderService:
    def build(self, events: list[dict]) -> dict:
        points: list[GovernanceTracePoint] = []
        for ev in events:
            points.append(
                GovernanceTracePoint(
                    ts=str(ev.get("ts") or ""),
                    stage=str(ev.get("stage") or "unknown"),
                    score=float(ev.get("score") or 0.0),
                    decision=str(ev.get("decision") or "unknown"),
                )
            )

        trend = "flat"
        if len(points) >= 2:
            first = points[0].score
            last = points[-1].score
            if last > first + 5:
                trend = "up"
            elif last < first - 5:
                trend = "down"

        return {
            "trend": trend,
            "count": len(points),
            "timeline": [p.to_dict() for p in points],
        }

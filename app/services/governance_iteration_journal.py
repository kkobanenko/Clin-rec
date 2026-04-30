"""Track iteration journal entries for governance execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GovernanceIterationEntry:
    iteration: int
    started_at: str
    completed_at: str
    scope: str
    outcome: str

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "scope": self.scope,
            "outcome": self.outcome,
        }


class GovernanceIterationJournalService:
    def summarize(self, entries: list[dict]) -> dict:
        parsed = [
            GovernanceIterationEntry(
                iteration=int(item.get("iteration") or 0),
                started_at=str(item.get("started_at") or ""),
                completed_at=str(item.get("completed_at") or ""),
                scope=str(item.get("scope") or ""),
                outcome=str(item.get("outcome") or "unknown"),
            )
            for item in entries
        ]
        total = len(parsed)
        completed = sum(1 for e in parsed if e.outcome in {"done", "ok", "completed"})
        failed = sum(1 for e in parsed if e.outcome in {"failed", "error"})
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "completion_rate": round((completed / total * 100.0), 2) if total else 0.0,
            "entries": [e.to_dict() for e in parsed],
        }

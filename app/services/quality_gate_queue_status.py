"""Queue status service for quality gate notification spool."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class QueueItemSummary:
    """Compact representation of one queued notification payload."""

    filename: str
    created_at: str
    age_seconds: float
    size_bytes: int
    verdict: str
    rules_failed: int
    rules_warn: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "created_at": self.created_at,
            "age_seconds": round(self.age_seconds, 2),
            "size_bytes": self.size_bytes,
            "verdict": self.verdict,
            "rules_failed": self.rules_failed,
            "rules_warn": self.rules_warn,
        }


@dataclass
class QueueStatusReport:
    """Aggregate queue status for operator monitoring."""

    spool_dir: str
    queue_size: int
    oldest_age_seconds: float
    newest_age_seconds: float
    total_size_bytes: int
    verdict_counters: dict[str, int] = field(default_factory=dict)
    items: list[QueueItemSummary] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spool_dir": self.spool_dir,
            "queue_size": self.queue_size,
            "oldest_age_seconds": round(self.oldest_age_seconds, 2),
            "newest_age_seconds": round(self.newest_age_seconds, 2),
            "total_size_bytes": self.total_size_bytes,
            "verdict_counters": self.verdict_counters,
            "items": [item.to_dict() for item in self.items],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Notification Queue Status",
            "",
            f"- spool_dir: `{self.spool_dir}`",
            f"- queue_size: **{self.queue_size}**",
            f"- total_size_bytes: **{self.total_size_bytes}**",
            f"- oldest_age_seconds: **{self.oldest_age_seconds:.1f}**",
            f"- newest_age_seconds: **{self.newest_age_seconds:.1f}**",
            "",
            "## Verdict Counters",
            "",
        ]
        for verdict, count in sorted(self.verdict_counters.items()):
            lines.append(f"- {verdict}: {count}")

        if self.items:
            lines.extend(
                [
                    "",
                    "## Queue Items",
                    "",
                    "| filename | age_seconds | size_bytes | verdict | failed | warn |",
                    "|---|---:|---:|---|---:|---:|",
                ]
            )
            for item in self.items:
                lines.append(
                    "| {filename} | {age:.1f} | {size} | {verdict} | {failed} | {warn} |".format(
                        filename=item.filename,
                        age=item.age_seconds,
                        size=item.size_bytes,
                        verdict=item.verdict,
                        failed=item.rules_failed,
                        warn=item.rules_warn,
                    )
                )
        return "\n".join(lines)


class QualityGateQueueStatusService:
    """Compute queue status report from spool directory contents."""

    def generate_report(
        self,
        *,
        spool_dir: str = ".artifacts/quality_gate_notify_queue",
        max_items: int = 50,
        now: datetime | None = None,
    ) -> QueueStatusReport:
        now_utc = now or datetime.now(timezone.utc)
        path = Path(spool_dir)
        if not path.exists():
            return QueueStatusReport(
                spool_dir=str(path),
                queue_size=0,
                oldest_age_seconds=0.0,
                newest_age_seconds=0.0,
                total_size_bytes=0,
                verdict_counters={},
                items=[],
            )

        queue_files = sorted(item for item in path.iterdir() if item.is_file() and item.suffix == ".json")
        items: list[QueueItemSummary] = []
        verdict_counters: dict[str, int] = {}
        total_size = 0
        age_values: list[float] = []

        for queue_file in queue_files[: max(0, max_items)]:
            stat = queue_file.stat()
            modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            age_seconds = max(0.0, (now_utc - modified_at).total_seconds())
            total_size += int(stat.st_size)
            age_values.append(age_seconds)

            verdict = "unknown"
            rules_failed = 0
            rules_warn = 0
            try:
                payload = json.loads(queue_file.read_text(encoding="utf-8"))
                if isinstance(payload, dict):
                    verdict = str(payload.get("verdict") or "unknown")
                    rules_failed = int(payload.get("rules_failed") or 0)
                    rules_warn = int(payload.get("rules_warn") or 0)
            except Exception:
                verdict = "invalid_json"

            verdict_counters[verdict] = verdict_counters.get(verdict, 0) + 1
            items.append(
                QueueItemSummary(
                    filename=queue_file.name,
                    created_at=modified_at.isoformat(),
                    age_seconds=age_seconds,
                    size_bytes=int(stat.st_size),
                    verdict=verdict,
                    rules_failed=rules_failed,
                    rules_warn=rules_warn,
                )
            )

        oldest_age = max(age_values) if age_values else 0.0
        newest_age = min(age_values) if age_values else 0.0
        return QueueStatusReport(
            spool_dir=str(path),
            queue_size=len(queue_files),
            oldest_age_seconds=oldest_age,
            newest_age_seconds=newest_age,
            total_size_bytes=total_size,
            verdict_counters=verdict_counters,
            items=items,
        )
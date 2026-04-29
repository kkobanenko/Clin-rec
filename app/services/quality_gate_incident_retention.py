"""Retention policy evaluation and cleanup for incident registry JSONL."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass
class IncidentRetentionReport:
    total_items_before: int = 0
    total_items_after: int = 0
    removed_items: int = 0
    max_items: int = 1000
    max_age_days: int = 30
    oldest_kept_created_at: str = ""
    oldest_removed_created_at: str = ""
    dry_run: bool = True
    removed_reasons: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_items_before": self.total_items_before,
            "total_items_after": self.total_items_after,
            "removed_items": self.removed_items,
            "max_items": self.max_items,
            "max_age_days": self.max_age_days,
            "oldest_kept_created_at": self.oldest_kept_created_at,
            "oldest_removed_created_at": self.oldest_removed_created_at,
            "dry_run": self.dry_run,
            "removed_reasons": dict(self.removed_reasons),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Incident Registry Retention",
            "",
            f"- total_items_before: {self.total_items_before}",
            f"- total_items_after: {self.total_items_after}",
            f"- removed_items: {self.removed_items}",
            f"- max_items: {self.max_items}",
            f"- max_age_days: {self.max_age_days}",
            f"- dry_run: {self.dry_run}",
            f"- oldest_kept_created_at: {self.oldest_kept_created_at or 'n/a'}",
            f"- oldest_removed_created_at: {self.oldest_removed_created_at or 'n/a'}",
            "",
            "## Removed Reasons",
            "",
        ]
        if self.removed_reasons:
            for reason, count in sorted(self.removed_reasons.items()):
                lines.append(f"- {reason}: {count}")
        else:
            lines.append("- none")
        return "\n".join(lines)


class QualityGateIncidentRetentionService:
    """Apply retention policy to local incident registry JSONL file."""

    def evaluate_policy(
        self,
        *,
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        max_items: int = 1000,
        max_age_days: int = 30,
    ) -> IncidentRetentionReport:
        return self._process(
            registry_dir=registry_dir,
            max_items=max_items,
            max_age_days=max_age_days,
            apply_changes=False,
        )

    def apply_policy(
        self,
        *,
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        max_items: int = 1000,
        max_age_days: int = 30,
    ) -> IncidentRetentionReport:
        return self._process(
            registry_dir=registry_dir,
            max_items=max_items,
            max_age_days=max_age_days,
            apply_changes=True,
        )

    def _process(
        self,
        *,
        registry_dir: str,
        max_items: int,
        max_age_days: int,
        apply_changes: bool,
    ) -> IncidentRetentionReport:
        max_items = max(1, int(max_items))
        max_age_days = max(1, int(max_age_days))

        path = Path(registry_dir) / "incidents.jsonl"
        if not path.exists():
            return IncidentRetentionReport(max_items=max_items, max_age_days=max_age_days, dry_run=not apply_changes)

        all_items = self._load_items(path)
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=max_age_days)

        keep_candidates: list[dict[str, Any]] = []
        removed_items: list[dict[str, Any]] = []
        removed_reasons: dict[str, int] = {}

        for item in all_items:
            created_at = self._parse_created_at(item)
            if created_at and created_at < cutoff:
                removed_items.append(item)
                removed_reasons["max_age"] = removed_reasons.get("max_age", 0) + 1
                continue
            keep_candidates.append(item)

        if len(keep_candidates) > max_items:
            overflow = len(keep_candidates) - max_items
            overflow_items = keep_candidates[:overflow]
            keep_candidates = keep_candidates[overflow:]
            removed_items.extend(overflow_items)
            removed_reasons["max_items"] = removed_reasons.get("max_items", 0) + len(overflow_items)

        if apply_changes:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as fh:
                for item in keep_candidates:
                    fh.write(json.dumps(item, ensure_ascii=False) + "\n")

        oldest_kept = self._safe_created_at(keep_candidates[0]) if keep_candidates else ""
        oldest_removed = self._safe_created_at(removed_items[0]) if removed_items else ""

        return IncidentRetentionReport(
            total_items_before=len(all_items),
            total_items_after=len(keep_candidates),
            removed_items=len(removed_items),
            max_items=max_items,
            max_age_days=max_age_days,
            oldest_kept_created_at=oldest_kept,
            oldest_removed_created_at=oldest_removed,
            dry_run=not apply_changes,
            removed_reasons=removed_reasons,
        )

    @staticmethod
    def _load_items(path: Path) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except Exception:
                continue
            if isinstance(payload, dict):
                items.append(payload)
        return items

    @staticmethod
    def _safe_created_at(item: dict[str, Any]) -> str:
        return str(item.get("created_at") or "")

    @staticmethod
    def _parse_created_at(item: dict[str, Any]) -> datetime | None:
        value = str(item.get("created_at") or "").strip()
        if not value:
            return None
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(value)
        except Exception:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

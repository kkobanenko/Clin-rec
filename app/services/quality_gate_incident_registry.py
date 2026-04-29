"""File-backed registry for quality gate incident escalation events."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class IncidentRegistryReport:
    total_items: int = 0
    escalate_items: int = 0
    severity_counters: dict[str, int] = field(default_factory=dict)
    latest_created_at: str = ""
    items: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_items": self.total_items,
            "escalate_items": self.escalate_items,
            "severity_counters": dict(self.severity_counters),
            "latest_created_at": self.latest_created_at,
            "items": list(self.items),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Quality Gate Incident Registry",
            "",
            f"- total_items: {self.total_items}",
            f"- escalate_items: {self.escalate_items}",
            f"- latest_created_at: {self.latest_created_at or 'n/a'}",
            "",
            "## Severity Counters",
            "",
        ]

        if self.severity_counters:
            for key, value in sorted(self.severity_counters.items()):
                lines.append(f"- {key}: {value}")
        else:
            lines.append("- none")

        lines.extend(["", "## Recent Items", "", "| created_at | severity | escalate | reason |", "|---|---|---|---|"])

        if self.items:
            for item in self.items:
                lines.append(
                    "| {created_at} | {severity} | {escalate} | {reason} |".format(
                        created_at=item.get("created_at") or "n/a",
                        severity=item.get("severity") or "unknown",
                        escalate="yes" if item.get("should_escalate") else "no",
                        reason=str(item.get("reason") or "").replace("|", "/"),
                    )
                )
        else:
            lines.append("| n/a | n/a | n/a | no incidents recorded |")

        return "\n".join(lines)


class QualityGateIncidentRegistryService:
    """Store incident events in JSONL and provide aggregate reports."""

    def append_incident(
        self,
        *,
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        incident: dict[str, Any],
        source: str = "quality_gate_incident",
    ) -> Path:
        base = Path(registry_dir)
        base.mkdir(parents=True, exist_ok=True)
        record_path = base / "incidents.jsonl"

        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "severity": str(incident.get("severity") or "unknown"),
            "should_escalate": bool(incident.get("should_escalate")),
            "reason": str(incident.get("reason") or ""),
            "tags": list(incident.get("tags") or []),
            "actions": list(incident.get("actions") or []),
            "details": incident.get("details") if isinstance(incident.get("details"), dict) else {},
            "incident": incident,
        }

        with record_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        return record_path

    def generate_report(
        self,
        *,
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        max_items: int = 50,
    ) -> IncidentRegistryReport:
        record_path = Path(registry_dir) / "incidents.jsonl"
        if not record_path.exists():
            return IncidentRegistryReport()

        all_items = self._load_items(record_path)
        selected = all_items[-max_items:] if max_items > 0 else all_items

        severity_counters: dict[str, int] = {}
        escalate_items = 0
        latest_created_at = ""

        for item in all_items:
            severity = str(item.get("severity") or "unknown")
            severity_counters[severity] = severity_counters.get(severity, 0) + 1
            if item.get("should_escalate"):
                escalate_items += 1
            created_at = str(item.get("created_at") or "")
            if created_at and created_at > latest_created_at:
                latest_created_at = created_at

        return IncidentRegistryReport(
            total_items=len(all_items),
            escalate_items=escalate_items,
            severity_counters=severity_counters,
            latest_created_at=latest_created_at,
            items=selected,
        )

    @staticmethod
    def _load_items(path: Path) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except Exception:
                continue
            if isinstance(payload, dict):
                items.append(payload)
        return items

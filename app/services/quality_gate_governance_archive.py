"""Archive export service for governance artifacts."""

from __future__ import annotations

import json
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService
from app.services.quality_gate_governance_trends import QualityGateGovernanceTrendsService
from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService


@dataclass
class GovernanceArchiveReport:
    archive_path: str
    generated_at: str
    file_count: int
    total_bytes: int
    entries: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive_path": self.archive_path,
            "generated_at": self.generated_at,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "entries": self.entries,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Governance Archive Export",
            "",
            f"- archive_path: {self.archive_path}",
            f"- generated_at: {self.generated_at}",
            f"- file_count: {self.file_count}",
            f"- total_bytes: {self.total_bytes}",
            "",
            "## Entries",
            "",
            "| name | bytes |",
            "|---|---:|",
        ]
        if self.entries:
            for entry in self.entries:
                lines.append(f"| {entry.get('name')} | {entry.get('bytes')} |")
        else:
            lines.append("| n/a | 0 |")
        return "\n".join(lines)


class QualityGateGovernanceArchiveService:
    """Create archive bundle with governance reports."""

    def __init__(
        self,
        *,
        score_service: QualityGateGovernanceScoreService | None = None,
        trends_service: QualityGateGovernanceTrendsService | None = None,
        registry_service: QualityGateIncidentRegistryService | None = None,
    ):
        self._score = score_service or QualityGateGovernanceScoreService()
        self._trends = trends_service or QualityGateGovernanceTrendsService()
        self._registry = registry_service or QualityGateIncidentRegistryService()

    def export_archive(
        self,
        *,
        output_dir: str = ".artifacts/quality_gate_governance_archive",
        max_versions: int = 100,
        high_skip_threshold: float = 0.8,
        max_avg_skip_rate: float = 0.75,
        min_candidate_pairs: int = 1,
        spool_dir: str = ".artifacts/quality_gate_notify_queue",
        registry_dir: str = ".artifacts/quality_gate_incident_registry",
        max_items: int = 50,
        baseline_window: int = 10,
    ) -> GovernanceArchiveReport:
        ts = datetime.now(timezone.utc)
        ts_label = ts.strftime("%Y%m%dT%H%M%SZ")
        base = Path(output_dir)
        base.mkdir(parents=True, exist_ok=True)

        staging = base / f"bundle_{ts_label}"
        staging.mkdir(parents=True, exist_ok=True)

        score_report = self._score.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
        )
        trends_report = self._trends.evaluate(
            max_versions=max_versions,
            high_skip_threshold=high_skip_threshold,
            max_avg_skip_rate=max_avg_skip_rate,
            min_candidate_pairs=min_candidate_pairs,
            spool_dir=spool_dir,
            registry_dir=registry_dir,
            max_items=max_items,
            baseline_window=baseline_window,
        )
        registry_report = self._registry.generate_report(
            registry_dir=registry_dir,
            max_items=max_items,
        )

        payloads = {
            "governance_score.json": score_report.to_dict(),
            "governance_trends.json": trends_report.to_dict(),
            "incident_registry.json": registry_report.to_dict(),
            "manifest.json": {
                "generated_at": ts.isoformat(),
                "max_versions": max_versions,
                "max_items": max_items,
                "baseline_window": baseline_window,
            },
        }

        entries: list[dict[str, Any]] = []
        total_bytes = 0
        for filename, payload in payloads.items():
            path = staging / filename
            content = json.dumps(payload, ensure_ascii=False, indent=2)
            path.write_text(content, encoding="utf-8")
            size = path.stat().st_size
            entries.append({"name": filename, "bytes": size})
            total_bytes += size

        archive_path = base / f"governance_bundle_{ts_label}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for entry in entries:
                tar.add(staging / entry["name"], arcname=entry["name"])

        return GovernanceArchiveReport(
            archive_path=str(archive_path),
            generated_at=ts.isoformat(),
            file_count=len(entries),
            total_bytes=total_bytes,
            entries=entries,
        )

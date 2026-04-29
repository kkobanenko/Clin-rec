"""Compare two governance snapshots exported in JSON format."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SnapshotCompareReport:
    baseline_path: str
    candidate_path: str
    status: str
    summary: str
    score_baseline: float
    score_candidate: float
    score_delta: float
    escalated_ratio_baseline: float
    escalated_ratio_candidate: float
    escalated_ratio_delta: float
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_path": self.baseline_path,
            "candidate_path": self.candidate_path,
            "status": self.status,
            "summary": self.summary,
            "score_baseline": round(self.score_baseline, 2),
            "score_candidate": round(self.score_candidate, 2),
            "score_delta": round(self.score_delta, 2),
            "escalated_ratio_baseline": round(self.escalated_ratio_baseline, 4),
            "escalated_ratio_candidate": round(self.escalated_ratio_candidate, 4),
            "escalated_ratio_delta": round(self.escalated_ratio_delta, 4),
            "findings": self.findings,
        }

    def to_markdown(self) -> str:
        lines = [
            "# Governance Snapshot Compare",
            "",
            f"- baseline_path: {self.baseline_path}",
            f"- candidate_path: {self.candidate_path}",
            f"- status: {self.status}",
            "",
            self.summary,
            "",
            f"- score_baseline: {self.score_baseline:.2f}",
            f"- score_candidate: {self.score_candidate:.2f}",
            f"- score_delta: {self.score_delta:.2f}",
            f"- escalated_ratio_baseline: {self.escalated_ratio_baseline:.4f}",
            f"- escalated_ratio_candidate: {self.escalated_ratio_candidate:.4f}",
            f"- escalated_ratio_delta: {self.escalated_ratio_delta:.4f}",
            "",
            "## Findings",
            "",
        ]
        if self.findings:
            lines.extend([f"- {item}" for item in self.findings])
        else:
            lines.append("- none")
        return "\n".join(lines)


class QualityGateGovernanceSnapshotCompareService:
    """Compare governance snapshot JSON payloads."""

    def compare(
        self,
        *,
        baseline_file: str,
        candidate_file: str,
    ) -> SnapshotCompareReport:
        baseline = self._read_json(Path(baseline_file))
        candidate = self._read_json(Path(candidate_file))

        score_baseline = float((baseline.get("governance_score") or {}).get("score") or 0.0)
        score_candidate = float((candidate.get("governance_score") or {}).get("score") or 0.0)
        score_delta = score_candidate - score_baseline

        ratio_baseline = self._escalated_ratio(baseline.get("incident_registry") or {})
        ratio_candidate = self._escalated_ratio(candidate.get("incident_registry") or {})
        ratio_delta = ratio_candidate - ratio_baseline

        findings: list[str] = []
        if score_delta >= 5:
            findings.append("Governance score improved significantly.")
        elif score_delta <= -5:
            findings.append("Governance score regressed significantly.")

        if ratio_delta >= 0.1:
            findings.append("Escalated incident ratio increased materially.")
        elif ratio_delta <= -0.1:
            findings.append("Escalated incident ratio improved materially.")

        if score_delta <= -5 or ratio_delta >= 0.1:
            status = "degrading"
            summary = "Candidate snapshot indicates governance degradation."
        elif score_delta >= 5 and ratio_delta <= 0:
            status = "improving"
            summary = "Candidate snapshot indicates governance improvement."
        else:
            status = "stable"
            summary = "Snapshot comparison indicates stable governance profile."

        return SnapshotCompareReport(
            baseline_path=baseline_file,
            candidate_path=candidate_file,
            status=status,
            summary=summary,
            score_baseline=score_baseline,
            score_candidate=score_candidate,
            score_delta=score_delta,
            escalated_ratio_baseline=ratio_baseline,
            escalated_ratio_candidate=ratio_candidate,
            escalated_ratio_delta=ratio_delta,
            findings=findings,
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"Snapshot is not an object: {path}")
        return payload

    @staticmethod
    def _escalated_ratio(registry: dict[str, Any]) -> float:
        total = float(registry.get("total_items") or 0.0)
        escalated = float(registry.get("escalate_items") or 0.0)
        if total <= 0:
            return 0.0
        return escalated / total

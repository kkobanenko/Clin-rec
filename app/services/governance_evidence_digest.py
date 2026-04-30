"""Governance evidence digest aggregation utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceDigestEntry:
    source: str
    title: str
    status: str
    weight: float
    details: dict[str, Any] = field(default_factory=dict)

    def score(self) -> float:
        if self.status == "pass":
            return 100.0 * self.weight
        if self.status == "warn":
            return 60.0 * self.weight
        if self.status == "fail":
            return 10.0 * self.weight
        return 30.0 * self.weight

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "title": self.title,
            "status": self.status,
            "weight": round(self.weight, 4),
            "score": round(self.score(), 2),
            "details": self.details,
        }


@dataclass
class GovernanceEvidenceDigestReport:
    verdict: str
    total_score: float
    max_score: float
    normalized_score: float
    summary: str
    entries: list[EvidenceDigestEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "total_score": round(self.total_score, 2),
            "max_score": round(self.max_score, 2),
            "normalized_score": round(self.normalized_score, 2),
            "summary": self.summary,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    def to_markdown(self) -> str:
        lines = [
            "# Governance Evidence Digest",
            "",
            f"- verdict: {self.verdict}",
            f"- total_score: {self.total_score:.2f}",
            f"- max_score: {self.max_score:.2f}",
            f"- normalized_score: {self.normalized_score:.2f}",
            "",
            self.summary,
            "",
            "## Entries",
            "",
            "| source | title | status | weight | score |",
            "|---|---|---|---:|---:|",
        ]
        if self.entries:
            for entry in self.entries:
                lines.append(
                    f"| {entry.source} | {entry.title} | {entry.status} | {entry.weight:.4f} | {entry.score():.2f} |"
                )
        else:
            lines.append("| n/a | n/a | n/a | 0.0000 | 0.00 |")
        return "\n".join(lines)


class GovernanceEvidenceDigestService:
    """Compute compact digest over governance evidence signals."""

    def build_digest(self, entries: list[dict[str, Any]]) -> GovernanceEvidenceDigestReport:
        parsed = [self._parse_entry(item) for item in entries]
        max_score = sum(100.0 * item.weight for item in parsed)
        total_score = sum(item.score() for item in parsed)
        normalized = (total_score / max_score * 100.0) if max_score > 0 else 0.0

        if normalized >= 85:
            verdict = "strong"
            summary = "Governance evidence is strong and internally consistent."
        elif normalized >= 60:
            verdict = "moderate"
            summary = "Governance evidence is moderate; manual review is advised."
        else:
            verdict = "weak"
            summary = "Governance evidence is weak and requires remediation."

        return GovernanceEvidenceDigestReport(
            verdict=verdict,
            total_score=total_score,
            max_score=max_score,
            normalized_score=normalized,
            summary=summary,
            entries=parsed,
        )

    @staticmethod
    def _parse_entry(item: dict[str, Any]) -> EvidenceDigestEntry:
        return EvidenceDigestEntry(
            source=str(item.get("source") or "unknown"),
            title=str(item.get("title") or "untitled"),
            status=str(item.get("status") or "unknown"),
            weight=float(item.get("weight") or 0.0),
            details=item.get("details") if isinstance(item.get("details"), dict) else {},
        )

"""Tests for governance snapshot compare service."""

from __future__ import annotations

import json

from app.services.quality_gate_governance_snapshot_compare import QualityGateGovernanceSnapshotCompareService


def _write(path, score: float, total: int, escalated: int):
    payload = {
        "governance_score": {"score": score},
        "incident_registry": {"total_items": total, "escalate_items": escalated},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_snapshot_compare_improving(tmp_path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    _write(baseline, 70.0, 10, 5)
    _write(candidate, 80.0, 10, 3)

    svc = QualityGateGovernanceSnapshotCompareService()
    report = svc.compare(baseline_file=str(baseline), candidate_file=str(candidate))
    assert report.status in {"improving", "stable"}


def test_snapshot_compare_degrading(tmp_path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    _write(baseline, 80.0, 10, 2)
    _write(candidate, 65.0, 10, 6)

    svc = QualityGateGovernanceSnapshotCompareService()
    report = svc.compare(baseline_file=str(baseline), candidate_file=str(candidate))
    assert report.status == "degrading"


def test_snapshot_compare_markdown_contains_sections(tmp_path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    _write(baseline, 80.0, 10, 2)
    _write(candidate, 79.0, 10, 2)

    svc = QualityGateGovernanceSnapshotCompareService()
    report = svc.compare(baseline_file=str(baseline), candidate_file=str(candidate))
    md = report.to_markdown()
    assert "# Governance Snapshot Compare" in md
    assert "## Findings" in md

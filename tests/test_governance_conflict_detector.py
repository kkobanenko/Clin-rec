"""Tests for governance conflict detector."""

from __future__ import annotations

from app.services.governance_conflict_detector import GovernanceConflictDetectorService


def test_conflict_detector_detects_conflict():
    svc = GovernanceConflictDetectorService()
    report = svc.detect({
        "score_status": "critical",
        "trend_status": "degrading",
        "adaptive_mode": "tighten",
        "decision": "allow",
    })
    assert report["count"] >= 1


def test_conflict_detector_markdown():
    svc = GovernanceConflictDetectorService()
    md = svc.to_markdown({"decision": "allow"})
    assert "# Governance Conflict Detector" in md

"""Tests for governance release guard."""

from __future__ import annotations

from app.services.governance_release_guard import GovernanceReleaseGuardService


def test_release_guard_blocks_on_low_score():
    svc = GovernanceReleaseGuardService()
    report = svc.evaluate({"normalized_score": 40})
    assert report["decision"] == "block"


def test_release_guard_allows_when_clean():
    svc = GovernanceReleaseGuardService()
    report = svc.evaluate(
        {
            "normalized_score": 90,
            "conflict_count": 0,
            "drift_severity": "low",
            "incident_open": False,
        }
    )
    assert report["decision"] == "allow"

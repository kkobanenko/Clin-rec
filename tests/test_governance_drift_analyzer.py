"""Tests for governance drift analyzer."""

from __future__ import annotations

from app.services.governance_drift_analyzer import GovernanceDriftAnalyzerService


def test_drift_analyzer_severity():
    svc = GovernanceDriftAnalyzerService()
    report = svc.analyze({"a": 0}, {"a": 30})
    assert report["severity"] in {"medium", "high", "low"}
    assert report["absolute_delta_sum"] >= 30

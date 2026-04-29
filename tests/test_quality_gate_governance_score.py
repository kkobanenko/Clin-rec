"""Tests for governance score service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_governance_score import QualityGateGovernanceScoreService


class _Fake:
    def __init__(self, payload):
        self._payload = payload

    def evaluate(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: self._payload)

    def generate_report(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: self._payload)


def test_governance_score_good_status():
    svc = QualityGateGovernanceScoreService(
        gate_service=_Fake({"verdict": "pass", "summary": "ok"}),
        queue_policy_service=_Fake({"verdict": "healthy", "summary": "ok"}),
        incident_service=_Fake({"severity": "info", "should_escalate": False, "reason": "ok"}),
        registry_service=_Fake({"total_items": 5, "escalate_items": 1}),
    )

    report = svc.evaluate()
    assert report.status == "good"
    assert report.score >= 85


def test_governance_score_warning_status():
    svc = QualityGateGovernanceScoreService(
        gate_service=_Fake({"verdict": "warn", "summary": "warn"}),
        queue_policy_service=_Fake({"verdict": "degraded", "summary": "warn"}),
        incident_service=_Fake({"severity": "high", "should_escalate": True, "reason": "risk"}),
        registry_service=_Fake({"total_items": 10, "escalate_items": 5}),
    )

    report = svc.evaluate()
    assert report.status in {"warning", "critical"}


def test_governance_score_markdown_contains_table():
    svc = QualityGateGovernanceScoreService(
        gate_service=_Fake({"verdict": "pass", "summary": "ok"}),
        queue_policy_service=_Fake({"verdict": "healthy", "summary": "ok"}),
        incident_service=_Fake({"severity": "info", "should_escalate": False, "reason": "ok"}),
        registry_service=_Fake({"total_items": 1, "escalate_items": 0}),
    )

    report = svc.evaluate()
    md = report.to_markdown()
    assert "# Quality Gate Governance Score" in md
    assert "## Components" in md
    assert "| Component | Verdict | Score | Weight | Weighted |" in md

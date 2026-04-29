"""Tests for quality gate incident escalation service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_incident import QualityGateIncidentService


class _FakeGateService:
    def __init__(self, payload):
        self._payload = payload

    def evaluate(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: self._payload)


class _FakeQueuePolicyService:
    def __init__(self, payload):
        self._payload = payload

    def evaluate(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: self._payload)


def _queue_payload(verdict: str) -> dict:
    return {
        "verdict": verdict,
        "summary": "queue summary",
        "queue_status": {
            "queue_size": 3,
            "oldest_age_seconds": 15,
        },
    }


def test_incident_report_info_for_pass_and_healthy():
    svc = QualityGateIncidentService(
        gate_service=_FakeGateService({"verdict": "pass", "summary": "ok"}),
        queue_policy_service=_FakeQueuePolicyService(_queue_payload("healthy")),
    )

    report = svc.evaluate()
    assert report.should_escalate is False
    assert report.severity == "info"


def test_incident_report_high_for_warn_or_degraded():
    svc = QualityGateIncidentService(
        gate_service=_FakeGateService({"verdict": "warn", "summary": "warn summary"}),
        queue_policy_service=_FakeQueuePolicyService(_queue_payload("degraded")),
    )

    report = svc.evaluate()
    assert report.should_escalate is True
    assert report.severity == "high"
    assert "Queue policy is degraded" in report.reason


def test_incident_report_critical_for_fail_or_critical_queue():
    svc = QualityGateIncidentService(
        gate_service=_FakeGateService({"verdict": "fail", "summary": "bad"}),
        queue_policy_service=_FakeQueuePolicyService(_queue_payload("critical")),
    )

    report = svc.evaluate()
    assert report.should_escalate is True
    assert report.severity == "critical"
    assert any("Stop release workflow" in action for action in report.actions)


def test_incident_markdown_contains_sections():
    svc = QualityGateIncidentService(
        gate_service=_FakeGateService({"verdict": "pass", "summary": "ok"}),
        queue_policy_service=_FakeQueuePolicyService(_queue_payload("healthy")),
    )

    report = svc.evaluate()
    md = report.to_markdown()
    assert "# Quality Gate Incident Escalation" in md
    assert "## Actions" in md
    assert "## Details" in md

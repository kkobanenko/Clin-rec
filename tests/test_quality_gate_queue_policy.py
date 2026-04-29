"""Tests for queue policy service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_queue_policy import QualityGateQueuePolicyService


class _FakeQueueStatusService:
    def __init__(self, payload):
        self._payload = payload

    def generate_report(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: self._payload)


def test_queue_policy_empty_verdict():
    svc = QualityGateQueuePolicyService(
        queue_status_service=_FakeQueueStatusService(
            {
                "queue_size": 0,
                "oldest_age_seconds": 0,
                "total_size_bytes": 0,
            }
        )
    )

    report = svc.evaluate()
    assert report.verdict == "empty"


def test_queue_policy_healthy_verdict():
    svc = QualityGateQueuePolicyService(
        queue_status_service=_FakeQueueStatusService(
            {
                "queue_size": 3,
                "oldest_age_seconds": 20,
                "total_size_bytes": 2000,
            }
        )
    )

    report = svc.evaluate()
    assert report.verdict == "healthy"


def test_queue_policy_degraded_verdict():
    svc = QualityGateQueuePolicyService(
        queue_status_service=_FakeQueueStatusService(
            {
                "queue_size": 25,
                "oldest_age_seconds": 300,
                "total_size_bytes": 4000,
            }
        )
    )

    report = svc.evaluate()
    assert report.verdict == "degraded"
    assert any(rule.status == "warn" for rule in report.rules)


def test_queue_policy_critical_verdict():
    svc = QualityGateQueuePolicyService(
        queue_status_service=_FakeQueueStatusService(
            {
                "queue_size": 220,
                "oldest_age_seconds": 5000,
                "total_size_bytes": 40000000,
            }
        )
    )

    report = svc.evaluate()
    assert report.verdict == "critical"
    assert any(rule.status == "fail" for rule in report.rules)


def test_queue_policy_markdown_contains_sections():
    svc = QualityGateQueuePolicyService(
        queue_status_service=_FakeQueueStatusService(
            {
                "queue_size": 25,
                "oldest_age_seconds": 300,
                "total_size_bytes": 4000,
            }
        )
    )

    report = svc.evaluate()
    md = report.to_markdown()
    assert "# Quality Gate Queue Policy" in md
    assert "## Rules" in md
    assert "## Recommended Actions" in md

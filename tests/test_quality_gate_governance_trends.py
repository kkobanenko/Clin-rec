"""Tests for governance trends service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_governance_trends import QualityGateGovernanceTrendsService


class _ScoreFake:
    def __init__(self, score):
        self._score = score

    def evaluate(self, **_kwargs):
        return SimpleNamespace(score=self._score)


class _RegistryFake:
    def __init__(self, items):
        self._items = items

    def generate_report(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: {"items": self._items})


def test_trends_stable_with_flat_incidents():
    items = [
        {"created_at": "2026-01-01T00:00:00+00:00", "should_escalate": False},
        {"created_at": "2026-01-02T00:00:00+00:00", "should_escalate": False},
        {"created_at": "2026-01-03T00:00:00+00:00", "should_escalate": False},
    ]
    svc = QualityGateGovernanceTrendsService(score_service=_ScoreFake(90.0), registry_service=_RegistryFake(items))

    report = svc.evaluate(baseline_window=3)
    assert report.status in {"stable", "improving"}
    assert len(report.points) == 3


def test_trends_degrading_with_escalations():
    items = [
        {"created_at": "2026-01-01T00:00:00+00:00", "should_escalate": False},
        {"created_at": "2026-01-02T00:00:00+00:00", "should_escalate": True},
        {"created_at": "2026-01-03T00:00:00+00:00", "should_escalate": True},
        {"created_at": "2026-01-04T00:00:00+00:00", "should_escalate": True},
    ]
    svc = QualityGateGovernanceTrendsService(score_service=_ScoreFake(70.0), registry_service=_RegistryFake(items))

    report = svc.evaluate(baseline_window=4)
    assert report.status in {"degrading", "stable"}


def test_trends_markdown_contains_sections():
    svc = QualityGateGovernanceTrendsService(score_service=_ScoreFake(85.0), registry_service=_RegistryFake([]))
    report = svc.evaluate(baseline_window=2)
    md = report.to_markdown()

    assert "# Quality Gate Governance Trends" in md
    assert "## Trend Points" in md

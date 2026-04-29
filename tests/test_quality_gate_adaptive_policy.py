"""Tests for adaptive policy service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_adaptive_policy import QualityGateAdaptivePolicyService


class _ScoreFake:
    def __init__(self, score):
        self._score = score

    def evaluate(self, **_kwargs):
        return SimpleNamespace(score=self._score)


class _TrendsFake:
    def __init__(self, status):
        self._status = status

    def evaluate(self, **_kwargs):
        return SimpleNamespace(status=self._status)


def test_adaptive_policy_tighten_mode():
    svc = QualityGateAdaptivePolicyService(score_service=_ScoreFake(55.0), trends_service=_TrendsFake("degrading"))
    report = svc.recommend()
    assert report.mode == "tighten"
    assert len(report.recommendations) >= 1


def test_adaptive_policy_relax_mode():
    svc = QualityGateAdaptivePolicyService(score_service=_ScoreFake(92.0), trends_service=_TrendsFake("improving"))
    report = svc.recommend()
    assert report.mode == "relax"


def test_adaptive_policy_hold_mode():
    svc = QualityGateAdaptivePolicyService(score_service=_ScoreFake(75.0), trends_service=_TrendsFake("stable"))
    report = svc.recommend()
    assert report.mode == "hold"


def test_adaptive_policy_markdown_contains_sections():
    svc = QualityGateAdaptivePolicyService(score_service=_ScoreFake(75.0), trends_service=_TrendsFake("stable"))
    report = svc.recommend()
    md = report.to_markdown()
    assert "# Quality Gate Adaptive Policy" in md
    assert "## Recommendations" in md

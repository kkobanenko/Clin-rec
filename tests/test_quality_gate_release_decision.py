"""Tests for release decision service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_release_decision import QualityGateReleaseDecisionService


class _ScoreFake:
    def __init__(self, score, status):
        self._score = score
        self._status = status

    def evaluate(self, **_kwargs):
        return SimpleNamespace(score=self._score, status=self._status)


class _TrendsFake:
    def __init__(self, status, ratio_delta, score_delta=0.0):
        self._status = status
        self._ratio_delta = ratio_delta
        self._score_delta = score_delta

    def evaluate(self, **_kwargs):
        return SimpleNamespace(status=self._status, escalated_ratio_delta=self._ratio_delta, score_delta=self._score_delta)


class _AdaptiveFake:
    def __init__(self, mode):
        self._mode = mode

    def recommend(self, **_kwargs):
        return SimpleNamespace(mode=self._mode)


def test_release_decision_allow():
    svc = QualityGateReleaseDecisionService(
        score_service=_ScoreFake(90.0, "good"),
        trends_service=_TrendsFake("stable", 0.01),
        adaptive_service=_AdaptiveFake("hold"),
    )
    report = svc.evaluate()
    assert report.decision == "allow"


def test_release_decision_block():
    svc = QualityGateReleaseDecisionService(
        score_service=_ScoreFake(40.0, "critical"),
        trends_service=_TrendsFake("degrading", 0.3),
        adaptive_service=_AdaptiveFake("tighten"),
    )
    report = svc.evaluate()
    assert report.decision == "block"


def test_release_decision_review_on_tighten():
    svc = QualityGateReleaseDecisionService(
        score_service=_ScoreFake(80.0, "warning"),
        trends_service=_TrendsFake("stable", 0.05),
        adaptive_service=_AdaptiveFake("tighten"),
    )
    report = svc.evaluate()
    assert report.decision in {"review", "block"}


def test_release_decision_markdown_contains_sections():
    svc = QualityGateReleaseDecisionService(
        score_service=_ScoreFake(90.0, "good"),
        trends_service=_TrendsFake("stable", 0.01),
        adaptive_service=_AdaptiveFake("hold"),
    )
    report = svc.evaluate()
    md = report.to_markdown()
    assert "# Release Decision" in md
    assert "## Rules" in md

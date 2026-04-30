"""Tests for governance readiness window."""

from __future__ import annotations

from app.services.governance_readiness_window import GovernanceReadinessWindowService


def test_window_closed_when_incident_open():
    svc = GovernanceReadinessWindowService()
    rep = svc.calculate({"score": 90, "incident_open": True})
    assert rep["window"] == "closed"


def test_window_wide_when_high_score():
    svc = GovernanceReadinessWindowService()
    rep = svc.calculate({"score": 90, "incident_open": False, "degradation": False})
    assert rep["window"] == "wide"

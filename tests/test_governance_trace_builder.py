"""Tests for governance trace builder."""

from __future__ import annotations

from app.services.governance_trace_builder import GovernanceTraceBuilderService


def test_trace_builder_trend_up():
    svc = GovernanceTraceBuilderService()
    rep = svc.build([
        {"ts": "t1", "stage": "a", "score": 50, "decision": "allow"},
        {"ts": "t2", "stage": "b", "score": 70, "decision": "allow"},
    ])
    assert rep["trend"] == "up"
    assert rep["count"] == 2

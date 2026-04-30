"""Generated smoke checks for iteration 13 service."""

from __future__ import annotations

from app.services.governance_autonomous_iter_13 import GovernanceAutonomousIter13Service


def test_iteration_13_step_001_shape():
    svc = GovernanceAutonomousIter13Service()
    result = svc.execute_step_001({"source_score": 77.0, "evidence_weight": 1.0})
    assert result["iteration"] == 13
    assert result["step"] == 1
    assert result["verdict"] in {"strong", "moderate", "watch", "weak"}


def test_iteration_13_step_100_shape():
    svc = GovernanceAutonomousIter13Service()
    result = svc.execute_step_100({"source_score": 12.0, "conflict_count": 3})
    assert result["iteration"] == 13
    assert result["step"] == 100
    assert "details" in result

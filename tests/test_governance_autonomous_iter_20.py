"""Generated smoke checks for iteration 20 service."""

from __future__ import annotations

from app.services.governance_autonomous_iter_20 import GovernanceAutonomousIter20Service


def test_iteration_20_step_001_shape():
    svc = GovernanceAutonomousIter20Service()
    result = svc.execute_step_001({"source_score": 77.0, "evidence_weight": 1.0})
    assert result["iteration"] == 20
    assert result["step"] == 1
    assert result["verdict"] in {"strong", "moderate", "watch", "weak"}


def test_iteration_20_step_100_shape():
    svc = GovernanceAutonomousIter20Service()
    result = svc.execute_step_100({"source_score": 12.0, "conflict_count": 3})
    assert result["iteration"] == 20
    assert result["step"] == 100
    assert "details" in result

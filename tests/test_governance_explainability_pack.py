"""Tests for governance explainability pack."""

from __future__ import annotations

from app.services.governance_explainability_pack import GovernanceExplainabilityPackService


def test_explainability_pack_contains_rationale():
    svc = GovernanceExplainabilityPackService()
    rep = svc.build({"decision": "allow", "score": 88, "reasons": ["stable"], "conflicts": 0})
    assert rep["risk_label"] == "managed"
    assert "Decision:" in rep["rationale"]

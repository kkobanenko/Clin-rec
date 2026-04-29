"""Tests for scripts/quality_gate_governance_snapshot_compare_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_governance_snapshot_compare_check


class _Report:
    def __init__(self, status):
        self._status = status

    def to_dict(self):
        return {
            "status": self._status,
            "score_delta": -6.0,
            "escalated_ratio_delta": 0.2,
        }


def test_snapshot_compare_check_ok():
    with patch(
        "scripts.quality_gate_governance_snapshot_compare_check.QualityGateGovernanceSnapshotCompareService.compare",
        return_value=_Report("stable"),
    ):
        code = quality_gate_governance_snapshot_compare_check.run(["--baseline-file", "a", "--candidate-file", "b"])
    assert code == 0


def test_snapshot_compare_check_fail_on_degrading():
    with patch(
        "scripts.quality_gate_governance_snapshot_compare_check.QualityGateGovernanceSnapshotCompareService.compare",
        return_value=_Report("degrading"),
    ):
        code = quality_gate_governance_snapshot_compare_check.run(["--baseline-file", "a", "--candidate-file", "b"])
    assert code == 1


def test_snapshot_compare_check_error():
    with patch(
        "scripts.quality_gate_governance_snapshot_compare_check.QualityGateGovernanceSnapshotCompareService.compare",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_governance_snapshot_compare_check.run(["--baseline-file", "a", "--candidate-file", "b"])
    assert code == 2

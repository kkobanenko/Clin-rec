"""Tests for scripts/quality_gate_incident_retention_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_incident_retention_check


def _payload(removed_items: int, dry_run: bool = True) -> dict:
    return {
        "total_items_before": 10,
        "total_items_after": 10 - removed_items,
        "removed_items": removed_items,
        "dry_run": dry_run,
    }


class _Report:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


def test_retention_check_ok_on_dry_run(capsys):
    with patch(
        "scripts.quality_gate_incident_retention_check.QualityGateIncidentRetentionService.evaluate_policy",
        return_value=_Report(_payload(0, True)),
    ):
        code = quality_gate_incident_retention_check.run(["--registry-dir", "/tmp/x"])
    assert code == 0


def test_retention_check_fails_when_removals_required(capsys):
    with patch(
        "scripts.quality_gate_incident_retention_check.QualityGateIncidentRetentionService.evaluate_policy",
        return_value=_Report(_payload(2, True)),
    ):
        code = quality_gate_incident_retention_check.run(["--registry-dir", "/tmp/x", "--fail-on-removals"])
    assert code == 1


def test_retention_check_apply_path(capsys):
    with patch(
        "scripts.quality_gate_incident_retention_check.QualityGateIncidentRetentionService.apply_policy",
        return_value=_Report(_payload(1, False)),
    ):
        code = quality_gate_incident_retention_check.run(["--registry-dir", "/tmp/x", "--apply"])
    assert code == 0


def test_retention_check_returns_two_on_failure(capsys):
    with patch(
        "scripts.quality_gate_incident_retention_check.QualityGateIncidentRetentionService.evaluate_policy",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_incident_retention_check.run(["--registry-dir", "/tmp/x"])
    assert code == 2

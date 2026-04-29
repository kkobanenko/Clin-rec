"""Tests for scripts/quality_gate_incident_registry_update.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_incident_registry_update


def _payload(severity: str, should_escalate: bool) -> dict:
    return {
        "severity": severity,
        "should_escalate": should_escalate,
        "reason": "r",
        "tags": ["t"],
        "actions": ["a"],
        "details": {"x": 1},
    }


def test_registry_update_success(tmp_path, capsys):
    with patch(
        "scripts.quality_gate_incident_registry_update._fetch_incident_report",
        return_value=_payload("high", True),
    ):
        code = quality_gate_incident_registry_update.run(
            ["--api-base", "http://test", "--registry-dir", str(tmp_path / "reg")]
        )

    captured = capsys.readouterr()
    assert code == 0
    assert "persisted" in captured.out


def test_registry_update_returns_two_for_fetch_failure(tmp_path):
    with patch(
        "scripts.quality_gate_incident_registry_update._fetch_incident_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_incident_registry_update.run(
            ["--api-base", "http://test", "--registry-dir", str(tmp_path / "reg")]
        )

    assert code == 2


def test_registry_update_returns_one_for_persist_failure(tmp_path):
    with patch(
        "scripts.quality_gate_incident_registry_update._fetch_incident_report",
        return_value=_payload("critical", True),
    ):
        with patch(
            "scripts.quality_gate_incident_registry_update.QualityGateIncidentRegistryService.append_incident",
            side_effect=RuntimeError("disk-fail"),
        ):
            code = quality_gate_incident_registry_update.run(
                ["--api-base", "http://test", "--registry-dir", str(tmp_path / "reg")]
            )

    assert code == 1

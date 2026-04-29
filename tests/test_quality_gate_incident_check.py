"""Tests for scripts/quality_gate_incident_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_incident_check


def _payload(*, should_escalate: bool, severity: str):
    return {
        "should_escalate": should_escalate,
        "severity": severity,
        "reason": "reason",
    }


def test_incident_check_ok_for_info_when_allowed(capsys):
    with patch(
        "scripts.quality_gate_incident_check._fetch_report",
        return_value=_payload(should_escalate=False, severity="info"),
    ):
        code = quality_gate_incident_check.run(["--api-base", "http://test", "--allow-info"])

    assert code == 0


def test_incident_check_fails_for_critical(capsys):
    with patch(
        "scripts.quality_gate_incident_check._fetch_report",
        return_value=_payload(should_escalate=True, severity="critical"),
    ):
        code = quality_gate_incident_check.run(["--api-base", "http://test"])

    assert code == 1


def test_incident_check_fails_for_high_when_configured(capsys):
    with patch(
        "scripts.quality_gate_incident_check._fetch_report",
        return_value=_payload(should_escalate=True, severity="high"),
    ):
        code = quality_gate_incident_check.run(["--api-base", "http://test", "--fail-on-high"])

    assert code == 1


def test_incident_check_warn_for_high_when_not_configured(capsys):
    with patch(
        "scripts.quality_gate_incident_check._fetch_report",
        return_value=_payload(should_escalate=True, severity="high"),
    ):
        code = quality_gate_incident_check.run(["--api-base", "http://test"])

    assert code == 0


def test_incident_check_returns_two_for_fetch_failure(capsys):
    with patch(
        "scripts.quality_gate_incident_check._fetch_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_incident_check.run(["--api-base", "http://test"])

    assert code == 2

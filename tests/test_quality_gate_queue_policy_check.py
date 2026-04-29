"""Tests for scripts/quality_gate_queue_policy_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_queue_policy_check


def _payload(verdict: str):
    return {"verdict": verdict, "summary": "summary", "rules": []}


def test_run_returns_zero_for_healthy(capsys):
    with patch("scripts.quality_gate_queue_policy_check._fetch_report", return_value=_payload("healthy")):
        code = quality_gate_queue_policy_check.run(["--api-base", "http://test"])

    captured = capsys.readouterr()
    assert code == 0
    assert "queue-policy check: OK" in captured.out


def test_run_returns_one_for_critical(capsys):
    with patch("scripts.quality_gate_queue_policy_check._fetch_report", return_value=_payload("critical")):
        code = quality_gate_queue_policy_check.run(["--api-base", "http://test"])

    captured = capsys.readouterr()
    assert code == 1
    assert "FAILED" in captured.err


def test_run_returns_one_for_degraded_when_configured(capsys):
    with patch("scripts.quality_gate_queue_policy_check._fetch_report", return_value=_payload("degraded")):
        code = quality_gate_queue_policy_check.run(["--api-base", "http://test", "--fail-on-degraded"])

    assert code == 1


def test_run_returns_one_for_empty_when_not_allowed(capsys):
    with patch("scripts.quality_gate_queue_policy_check._fetch_report", return_value=_payload("empty")):
        code = quality_gate_queue_policy_check.run(["--api-base", "http://test"])

    assert code == 1


def test_run_returns_zero_for_empty_when_allowed(capsys):
    with patch("scripts.quality_gate_queue_policy_check._fetch_report", return_value=_payload("empty")):
        code = quality_gate_queue_policy_check.run(["--api-base", "http://test", "--allow-empty"])

    assert code == 0


def test_run_returns_two_on_request_failure(capsys):
    with patch(
        "scripts.quality_gate_queue_policy_check._fetch_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_queue_policy_check.run(["--api-base", "http://test"])

    assert code == 2

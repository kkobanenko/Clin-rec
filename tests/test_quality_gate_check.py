"""Tests for scripts/quality_gate_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_check


def test_should_fail_policy_matrix():
    assert quality_gate_check._should_fail("fail", quality_gate_check.GatePolicy()) is True
    assert quality_gate_check._should_fail("unknown", quality_gate_check.GatePolicy()) is True
    assert quality_gate_check._should_fail("warn", quality_gate_check.GatePolicy(fail_on_warn=True)) is True
    assert quality_gate_check._should_fail("warn", quality_gate_check.GatePolicy(fail_on_warn=False)) is False
    assert quality_gate_check._should_fail("no-data", quality_gate_check.GatePolicy(fail_on_no_data=True)) is True
    assert quality_gate_check._should_fail("no-data", quality_gate_check.GatePolicy(fail_on_no_data=False)) is False


def test_run_pass_verdict_returns_zero(capsys):
    payload = {
        "verdict": "pass",
        "summary": "all rules are green",
        "rules": [
            {
                "name": "avg_skip_rate",
                "status": "pass",
                "value": 0.3,
                "comparator": "<=",
                "threshold": 0.75,
            }
        ],
    }
    with patch("scripts.quality_gate_check._request_report", return_value=payload):
        code = quality_gate_check.run(["--api-base", "http://test"])

    captured = capsys.readouterr()
    assert code == 0
    assert "quality-gate verdict: pass" in captured.out
    assert "quality-gate policy: OK" in captured.out


def test_run_warn_with_fail_on_warn_returns_one(capsys):
    payload = {
        "verdict": "warn",
        "summary": "warning",
        "rules": [],
    }
    with patch("scripts.quality_gate_check._request_report", return_value=payload):
        code = quality_gate_check.run(["--api-base", "http://test", "--fail-on-warn"])

    captured = capsys.readouterr()
    assert code == 1
    assert "quality-gate policy: FAILED" in captured.err


def test_run_no_data_allowed_returns_zero(capsys):
    payload = {
        "verdict": "no-data",
        "summary": "pipeline has not produced events yet",
        "rules": [],
    }
    with patch("scripts.quality_gate_check._request_report", return_value=payload):
        code = quality_gate_check.run(["--api-base", "http://test", "--allow-no-data"])

    captured = capsys.readouterr()
    assert code == 0
    assert "quality-gate policy: OK" in captured.out


def test_run_emits_json_payload_when_requested(capsys):
    payload = {
        "verdict": "pass",
        "summary": "ok",
        "rules": [],
    }
    with patch("scripts.quality_gate_check._request_report", return_value=payload):
        code = quality_gate_check.run(["--api-base", "http://test", "--json"])

    captured = capsys.readouterr()
    assert code == 0
    assert '"verdict": "pass"' in captured.out


def test_run_returns_two_on_http_error(capsys):
    with patch(
        "scripts.quality_gate_check._request_report",
        side_effect=quality_gate_check.httpx.ConnectError("boom"),
    ):
        code = quality_gate_check.run(["--api-base", "http://test"])

    captured = capsys.readouterr()
    assert code == 2
    assert "quality-gate: API request failed" in captured.err

"""Tests for scripts/quality_gate_adaptive_policy_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_adaptive_policy_check


def _payload(mode: str) -> dict:
    return {"mode": mode, "recommendations": []}


def test_adaptive_policy_check_ok():
    with patch(
        "scripts.quality_gate_adaptive_policy_check._fetch_report",
        return_value=_payload("hold"),
    ):
        code = quality_gate_adaptive_policy_check.run(["--api-base", "http://test"])
    assert code == 0


def test_adaptive_policy_check_fail_on_tighten():
    with patch(
        "scripts.quality_gate_adaptive_policy_check._fetch_report",
        return_value=_payload("tighten"),
    ):
        code = quality_gate_adaptive_policy_check.run(["--api-base", "http://test", "--fail-on-mode", "tighten"])
    assert code == 1


def test_adaptive_policy_check_fetch_error():
    with patch(
        "scripts.quality_gate_adaptive_policy_check._fetch_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_adaptive_policy_check.run(["--api-base", "http://test"])
    assert code == 2

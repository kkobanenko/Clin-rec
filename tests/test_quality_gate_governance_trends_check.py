"""Tests for scripts/quality_gate_governance_trends_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_governance_trends_check


def _payload(status: str) -> dict:
    return {"status": status, "score_delta": -1.5, "escalated_ratio_delta": 0.25}


def test_trends_check_ok_for_stable():
    with patch(
        "scripts.quality_gate_governance_trends_check._fetch_report",
        return_value=_payload("stable"),
    ):
        code = quality_gate_governance_trends_check.run(["--api-base", "http://test"])

    assert code == 0


def test_trends_check_fails_for_degrading():
    with patch(
        "scripts.quality_gate_governance_trends_check._fetch_report",
        return_value=_payload("degrading"),
    ):
        code = quality_gate_governance_trends_check.run(["--api-base", "http://test"])

    assert code == 1


def test_trends_check_returns_two_on_failure():
    with patch(
        "scripts.quality_gate_governance_trends_check._fetch_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_governance_trends_check.run(["--api-base", "http://test"])

    assert code == 2

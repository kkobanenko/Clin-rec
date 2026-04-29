"""Tests for scripts/quality_gate_release_decision_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_release_decision_check


def _payload(decision: str) -> dict:
    return {"decision": decision, "confidence": 0.9}


def test_release_decision_check_ok():
    with patch(
        "scripts.quality_gate_release_decision_check._fetch_report",
        return_value=_payload("allow"),
    ):
        code = quality_gate_release_decision_check.run(["--api-base", "http://test"])
    assert code == 0


def test_release_decision_check_fail_on_block():
    with patch(
        "scripts.quality_gate_release_decision_check._fetch_report",
        return_value=_payload("block"),
    ):
        code = quality_gate_release_decision_check.run(["--api-base", "http://test", "--fail-on-decision", "block"])
    assert code == 1


def test_release_decision_check_error():
    with patch(
        "scripts.quality_gate_release_decision_check._fetch_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_release_decision_check.run(["--api-base", "http://test"])
    assert code == 2

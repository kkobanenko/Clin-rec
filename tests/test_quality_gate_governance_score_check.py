"""Tests for scripts/quality_gate_governance_score_check.py."""

from __future__ import annotations

from unittest.mock import patch

from scripts import quality_gate_governance_score_check


def _payload(score: float, status: str) -> dict:
    return {"score": score, "status": status}


def test_governance_score_check_ok(capsys):
    with patch(
        "scripts.quality_gate_governance_score_check._fetch_report",
        return_value=_payload(88.5, "good"),
    ):
        code = quality_gate_governance_score_check.run(["--api-base", "http://test", "--min-score", "60"])

    assert code == 0


def test_governance_score_check_fails_below_threshold(capsys):
    with patch(
        "scripts.quality_gate_governance_score_check._fetch_report",
        return_value=_payload(55.0, "warning"),
    ):
        code = quality_gate_governance_score_check.run(["--api-base", "http://test", "--min-score", "60"])

    assert code == 1


def test_governance_score_check_returns_two_on_failure(capsys):
    with patch(
        "scripts.quality_gate_governance_score_check._fetch_report",
        side_effect=RuntimeError("boom"),
    ):
        code = quality_gate_governance_score_check.run(["--api-base", "http://test"])

    assert code == 2

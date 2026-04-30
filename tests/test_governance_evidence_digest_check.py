"""Tests for governance_evidence_digest_check CLI."""

from __future__ import annotations

import json

from scripts import governance_evidence_digest_check


def test_digest_check_ok(tmp_path):
    path = tmp_path / "entries.json"
    path.write_text(
        json.dumps(
            [
                {"source": "score", "title": "Score", "status": "pass", "weight": 1.0},
            ]
        ),
        encoding="utf-8",
    )
    code = governance_evidence_digest_check.run(["--input-json", str(path), "--min-score", "50"])
    assert code == 0


def test_digest_check_fail_threshold(tmp_path):
    path = tmp_path / "entries.json"
    path.write_text(
        json.dumps(
            [
                {"source": "score", "title": "Score", "status": "fail", "weight": 1.0},
            ]
        ),
        encoding="utf-8",
    )
    code = governance_evidence_digest_check.run(["--input-json", str(path), "--min-score", "80"])
    assert code == 1


def test_digest_check_invalid_payload(tmp_path):
    path = tmp_path / "entries.json"
    path.write_text(json.dumps({"bad": True}), encoding="utf-8")
    code = governance_evidence_digest_check.run(["--input-json", str(path)])
    assert code == 2

"""Tests for scripts/quality_gate_notify_drain.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts import quality_gate_notify_drain


def _write_queue_item(spool_dir: Path, name: str, payload: dict):
    spool_dir.mkdir(parents=True, exist_ok=True)
    (spool_dir / name).write_text(json.dumps(payload), encoding="utf-8")


def test_run_skips_when_webhook_missing_and_allowed(tmp_path: Path, capsys):
    code = quality_gate_notify_drain.run([
        "--spool-dir",
        str(tmp_path / "queue"),
        "--allow-missing-webhook",
    ])
    captured = capsys.readouterr()

    assert code == 0
    assert "skipping" in captured.out


def test_run_returns_two_when_webhook_missing_required(tmp_path: Path, capsys):
    code = quality_gate_notify_drain.run(["--spool-dir", str(tmp_path / "queue")])
    captured = capsys.readouterr()

    assert code == 2
    assert "webhook URL missing" in captured.err


def test_run_delivers_and_removes_queue_file(tmp_path: Path, capsys):
    spool_dir = tmp_path / "queue"
    _write_queue_item(spool_dir, "item1.json", {"verdict": "warn"})

    class _Resp:
        def raise_for_status(self):
            return None

    with patch("scripts.quality_gate_notify_drain.httpx.post", return_value=_Resp()):
        code = quality_gate_notify_drain.run([
            "--spool-dir",
            str(spool_dir),
            "--webhook-url",
            "http://webhook",
            "--max-items",
            "10",
        ])

    captured = capsys.readouterr()
    assert code == 0
    assert "delivered item1.json" in captured.out
    assert list(spool_dir.glob("*.json")) == []


def test_run_returns_one_on_delivery_failure(tmp_path: Path, capsys):
    spool_dir = tmp_path / "queue"
    _write_queue_item(spool_dir, "item1.json", {"verdict": "fail"})

    with patch(
        "scripts.quality_gate_notify_drain.httpx.post",
        side_effect=quality_gate_notify_drain.httpx.ConnectError("boom"),
    ):
        code = quality_gate_notify_drain.run([
            "--spool-dir",
            str(spool_dir),
            "--webhook-url",
            "http://webhook",
            "--retries",
            "0",
        ])

    captured = capsys.readouterr()
    assert code == 1
    assert "failed item1.json" in captured.err
    assert len(list(spool_dir.glob("*.json"))) == 1


def test_run_soft_fail_on_delivery_failure(tmp_path: Path, capsys):
    spool_dir = tmp_path / "queue"
    _write_queue_item(spool_dir, "item1.json", {"verdict": "fail"})

    with patch(
        "scripts.quality_gate_notify_drain.httpx.post",
        side_effect=quality_gate_notify_drain.httpx.ConnectError("boom"),
    ):
        code = quality_gate_notify_drain.run([
            "--spool-dir",
            str(spool_dir),
            "--webhook-url",
            "http://webhook",
            "--retries",
            "0",
            "--soft-fail",
        ])

    captured = capsys.readouterr()
    assert code == 0
    assert "failed item1.json" in captured.err

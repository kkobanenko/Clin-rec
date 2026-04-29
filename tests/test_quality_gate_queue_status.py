"""Tests for quality gate queue status service."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from app.services.quality_gate_queue_status import QualityGateQueueStatusService


def _write_item(spool_dir: Path, name: str, payload: dict):
    spool_dir.mkdir(parents=True, exist_ok=True)
    (spool_dir / name).write_text(json.dumps(payload), encoding="utf-8")


def test_generate_report_for_missing_dir(tmp_path: Path):
    svc = QualityGateQueueStatusService()
    report = svc.generate_report(spool_dir=str(tmp_path / "missing"))

    assert report.queue_size == 0
    assert report.total_size_bytes == 0
    assert report.items == []


def test_generate_report_with_queue_items(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    _write_item(spool_dir, "a.json", {"verdict": "warn", "rules_failed": 1, "rules_warn": 2})
    time.sleep(0.01)
    _write_item(spool_dir, "b.json", {"verdict": "pass", "rules_failed": 0, "rules_warn": 0})

    svc = QualityGateQueueStatusService()
    report = svc.generate_report(
        spool_dir=str(spool_dir),
        max_items=10,
        now=datetime.now(timezone.utc),
    )

    assert report.queue_size == 2
    assert report.total_size_bytes > 0
    assert report.oldest_age_seconds >= report.newest_age_seconds
    assert report.verdict_counters["warn"] == 1
    assert report.verdict_counters["pass"] == 1
    assert len(report.items) == 2


def test_generate_report_marks_invalid_json(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    spool_dir.mkdir(parents=True, exist_ok=True)
    (spool_dir / "bad.json").write_text("{broken", encoding="utf-8")

    svc = QualityGateQueueStatusService()
    report = svc.generate_report(spool_dir=str(spool_dir), max_items=10)

    assert report.queue_size == 1
    assert report.items[0].verdict == "invalid_json"


def test_generate_report_respects_max_items(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    for idx in range(5):
        _write_item(spool_dir, f"{idx}.json", {"verdict": "pass"})

    svc = QualityGateQueueStatusService()
    report = svc.generate_report(spool_dir=str(spool_dir), max_items=2)

    assert report.queue_size == 5
    assert len(report.items) == 2


def test_to_markdown_contains_header(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    _write_item(spool_dir, "a.json", {"verdict": "warn", "rules_failed": 1, "rules_warn": 0})

    svc = QualityGateQueueStatusService()
    report = svc.generate_report(spool_dir=str(spool_dir), max_items=10)
    md = report.to_markdown()

    assert "# Quality Gate Notification Queue Status" in md
    assert "Queue Items" in md

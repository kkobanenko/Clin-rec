"""Tests for file-backed quality gate delivery queue utilities."""

from __future__ import annotations

from pathlib import Path

from scripts.quality_gate_delivery_queue import (
    enqueue_payload,
    list_queue_files,
    load_payload,
    remove_payload,
)


def test_enqueue_and_load_payload(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    payload = {"event": "quality_gate_verdict", "verdict": "warn"}

    queue_file = enqueue_payload(spool_dir, payload)

    assert queue_file.exists()
    loaded = load_payload(queue_file)
    assert loaded == payload


def test_list_queue_files_sorted(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    enqueue_payload(spool_dir, {"idx": 1})
    enqueue_payload(spool_dir, {"idx": 2})

    items = list_queue_files(spool_dir)

    assert len(items) == 2
    assert items == sorted(items)


def test_remove_payload(tmp_path: Path):
    spool_dir = tmp_path / "queue"
    queue_file = enqueue_payload(spool_dir, {"idx": 1})
    assert queue_file.exists()

    remove_payload(queue_file)

    assert not queue_file.exists()


def test_list_queue_files_for_missing_dir(tmp_path: Path):
    spool_dir = tmp_path / "missing"
    assert list_queue_files(spool_dir) == []

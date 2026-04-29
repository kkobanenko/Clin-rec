"""Tests for incident registry retention service."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from app.services.quality_gate_incident_retention import QualityGateIncidentRetentionService


def _write_items(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")


def test_retention_evaluate_by_age_and_count(tmp_path):
    svc = QualityGateIncidentRetentionService()
    registry_file = tmp_path / "registry" / "incidents.jsonl"
    now = datetime.now(timezone.utc)

    items = []
    for idx in range(5):
        items.append(
            {
                "created_at": (now - timedelta(days=idx)).isoformat(),
                "severity": "high",
                "should_escalate": True,
            }
        )
    items.append(
        {
            "created_at": (now - timedelta(days=100)).isoformat(),
            "severity": "info",
            "should_escalate": False,
        }
    )

    _write_items(registry_file, items)
    report = svc.evaluate_policy(registry_dir=str(tmp_path / "registry"), max_items=3, max_age_days=30)

    assert report.total_items_before == 6
    assert report.total_items_after == 3
    assert report.removed_items == 3
    assert report.dry_run is True


def test_retention_apply_rewrites_registry(tmp_path):
    svc = QualityGateIncidentRetentionService()
    registry_file = tmp_path / "registry" / "incidents.jsonl"
    now = datetime.now(timezone.utc)

    items = []
    for idx in range(4):
        items.append(
            {
                "created_at": (now - timedelta(days=idx)).isoformat(),
                "severity": "high",
                "should_escalate": True,
            }
        )

    _write_items(registry_file, items)
    report = svc.apply_policy(registry_dir=str(tmp_path / "registry"), max_items=2, max_age_days=30)

    assert report.dry_run is False
    assert report.total_items_after == 2
    saved_lines = registry_file.read_text(encoding="utf-8").splitlines()
    assert len(saved_lines) == 2


def test_retention_markdown_contains_sections(tmp_path):
    svc = QualityGateIncidentRetentionService()
    report = svc.evaluate_policy(registry_dir=str(tmp_path / "missing"), max_items=2, max_age_days=7)
    md = report.to_markdown()

    assert "# Incident Registry Retention" in md
    assert "## Removed Reasons" in md

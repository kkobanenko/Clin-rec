"""Tests for governance signal normalizer."""

from __future__ import annotations

from app.services.governance_signal_normalizer import GovernanceSignalNormalizerService


def test_normalizer_range_mapping():
    svc = GovernanceSignalNormalizerService()
    items = svc.normalize([
        {"name": "score", "raw": 75, "min": 0, "max": 100},
        {"name": "ratio", "raw": 0.2, "min": 0, "max": 1},
    ])
    assert len(items) == 2
    assert 0 <= items[0].normalized <= 1


def test_normalizer_summary_fields():
    svc = GovernanceSignalNormalizerService()
    summary = svc.summarize([
        {"name": "x", "raw": 5, "min": 0, "max": 10},
    ])
    assert summary["count"] == 1
    assert "signals" in summary

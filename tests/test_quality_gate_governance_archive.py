"""Tests for governance archive service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate_governance_archive import QualityGateGovernanceArchiveService


class _FakeScore:
    def evaluate(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: {"score": 88.0, "status": "good"})


class _FakeTrends:
    def evaluate(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: {"status": "stable", "score_delta": 1.2})


class _FakeRegistry:
    def generate_report(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: {"total_items": 2, "escalate_items": 1})


def test_archive_export_creates_bundle(tmp_path):
    svc = QualityGateGovernanceArchiveService(
        score_service=_FakeScore(),
        trends_service=_FakeTrends(),
        registry_service=_FakeRegistry(),
    )

    report = svc.export_archive(output_dir=str(tmp_path / "archive"))
    payload = report.to_dict()

    assert payload["file_count"] >= 4
    assert payload["total_bytes"] > 0
    assert payload["archive_path"].endswith(".tar.gz")


def test_archive_markdown_contains_sections(tmp_path):
    svc = QualityGateGovernanceArchiveService(
        score_service=_FakeScore(),
        trends_service=_FakeTrends(),
        registry_service=_FakeRegistry(),
    )

    report = svc.export_archive(output_dir=str(tmp_path / "archive"))
    md = report.to_markdown()
    assert "# Governance Archive Export" in md
    assert "## Entries" in md

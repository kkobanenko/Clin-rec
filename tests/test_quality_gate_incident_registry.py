"""Tests for quality gate incident registry service."""

from __future__ import annotations

from app.services.quality_gate_incident_registry import QualityGateIncidentRegistryService


def _incident(severity: str, should_escalate: bool) -> dict:
    return {
        "severity": severity,
        "should_escalate": should_escalate,
        "reason": f"reason-{severity}",
        "tags": ["tag1"],
        "actions": ["act1"],
        "details": {"k": "v"},
    }


def test_registry_append_and_report(tmp_path):
    svc = QualityGateIncidentRegistryService()
    registry = tmp_path / "incidents"

    svc.append_incident(registry_dir=str(registry), incident=_incident("high", True), source="test")
    svc.append_incident(registry_dir=str(registry), incident=_incident("critical", True), source="test")
    svc.append_incident(registry_dir=str(registry), incident=_incident("info", False), source="test")

    report = svc.generate_report(registry_dir=str(registry), max_items=10)
    assert report.total_items == 3
    assert report.escalate_items == 2
    assert report.severity_counters["high"] == 1
    assert report.severity_counters["critical"] == 1
    assert report.severity_counters["info"] == 1
    assert len(report.items) == 3


def test_registry_report_handles_missing_file(tmp_path):
    svc = QualityGateIncidentRegistryService()
    report = svc.generate_report(registry_dir=str(tmp_path / "missing"), max_items=10)

    assert report.total_items == 0
    assert report.items == []


def test_registry_markdown_contains_sections(tmp_path):
    svc = QualityGateIncidentRegistryService()
    registry = tmp_path / "incidents"
    svc.append_incident(registry_dir=str(registry), incident=_incident("high", True), source="test")

    report = svc.generate_report(registry_dir=str(registry), max_items=10)
    md = report.to_markdown()
    assert "# Quality Gate Incident Registry" in md
    assert "## Severity Counters" in md
    assert "## Recent Items" in md

"""Unit tests for automated quality gate service."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.quality_gate import QualityGateService


class _FakeCQService:
    def __init__(self, payload):
        self._payload = payload

    def generate_report(self):
        return SimpleNamespace(to_dict=lambda: self._payload)


class _FakeCDService:
    def __init__(self, payload):
        self._payload = payload

    def generate_report(self, **_kwargs):
        return SimpleNamespace(to_dict=lambda: self._payload)


def test_quality_gate_pass_verdict():
    cq_payload = {
        "overall_health": "healthy",
        "flags": [],
    }
    cd_payload = {
        "versions_considered": 10,
        "avg_skip_rate": 0.2,
        "high_skip_versions": 1,
        "total_candidate_pairs": 20,
    }
    service = QualityGateService(
        corpus_quality_service=_FakeCQService(cq_payload),
        candidate_diagnostics_service=_FakeCDService(cd_payload),
    )

    report = service.evaluate(max_avg_skip_rate=0.75, min_candidate_pairs=1)

    assert report.verdict == "pass"
    assert len(report.rules) == 4
    assert any(rule.name == "avg_skip_rate" for rule in report.rules)


def test_quality_gate_warn_when_avg_skip_too_high():
    cq_payload = {
        "overall_health": "degraded",
        "flags": [{"metric": "image_fraction"}],
    }
    cd_payload = {
        "versions_considered": 8,
        "avg_skip_rate": 0.9,
        "high_skip_versions": 5,
        "total_candidate_pairs": 11,
    }
    service = QualityGateService(
        corpus_quality_service=_FakeCQService(cq_payload),
        candidate_diagnostics_service=_FakeCDService(cd_payload),
    )

    report = service.evaluate(max_avg_skip_rate=0.75, min_candidate_pairs=1)

    assert report.verdict == "warn"
    avg_rule = next(rule for rule in report.rules if rule.name == "avg_skip_rate")
    assert avg_rule.status == "warn"


def test_quality_gate_fail_when_corpus_health_critical_or_pairs_missing():
    cq_payload = {
        "overall_health": "critical",
        "flags": [{"metric": "evidence_coverage"}],
    }
    cd_payload = {
        "versions_considered": 5,
        "avg_skip_rate": 0.3,
        "high_skip_versions": 0,
        "total_candidate_pairs": 0,
    }
    service = QualityGateService(
        corpus_quality_service=_FakeCQService(cq_payload),
        candidate_diagnostics_service=_FakeCDService(cd_payload),
    )

    report = service.evaluate(max_avg_skip_rate=0.75, min_candidate_pairs=1)

    assert report.verdict == "fail"
    fail_rules = [rule for rule in report.rules if rule.status == "fail"]
    assert len(fail_rules) >= 2


def test_quality_gate_no_data_when_versions_absent():
    cq_payload = {
        "overall_health": "healthy",
        "flags": [],
    }
    cd_payload = {
        "versions_considered": 0,
        "avg_skip_rate": 0.0,
        "high_skip_versions": 0,
        "total_candidate_pairs": 0,
    }
    service = QualityGateService(
        corpus_quality_service=_FakeCQService(cq_payload),
        candidate_diagnostics_service=_FakeCDService(cd_payload),
    )

    report = service.evaluate(max_avg_skip_rate=0.75, min_candidate_pairs=1)

    assert report.verdict == "no-data"
    assert "No candidate diagnostics data" in report.summary


def test_quality_gate_markdown_contains_verdict_and_rules():
    cq_payload = {
        "overall_health": "healthy",
        "flags": [],
    }
    cd_payload = {
        "versions_considered": 10,
        "avg_skip_rate": 0.2,
        "high_skip_versions": 0,
        "total_candidate_pairs": 20,
    }
    service = QualityGateService(
        corpus_quality_service=_FakeCQService(cq_payload),
        candidate_diagnostics_service=_FakeCDService(cd_payload),
    )

    report = service.evaluate(max_avg_skip_rate=0.75, min_candidate_pairs=1)
    markdown = report.to_markdown()

    assert "# Automated Quality Gate" in markdown
    assert "**Verdict:** PASS" in markdown
    assert "## Rules" in markdown

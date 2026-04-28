"""Tests for ReleaseEvidenceReportService."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.evidence_report import (
    ArtifactCoverageRow,
    ReleaseEvidenceReport,
    ReleaseEvidenceReportService,
    SampleTraceabilityChain,
)
from app.schemas.diagnostics import EvidenceStateCountersOut


# ---- ReleaseEvidenceReport unit tests ----------------------------------------


class TestReleaseEvidenceReport:
    def _make_report(self, **kwargs) -> ReleaseEvidenceReport:
        defaults = dict(
            generated_at=datetime(2026, 4, 28, 10, 0, 0, tzinfo=timezone.utc),
            current_versions_total=10,
            versions_with_json_artifact=8,
            versions_with_normalized_content=8,
            json_derived_sections=300,
            json_derived_fragments=900,
            total_pair_evidence_rows=0,
            total_matrix_cells=0,
            active_model_version="v1.0",
        )
        defaults.update(kwargs)
        return ReleaseEvidenceReport(**defaults)

    def test_to_dict_has_required_keys(self):
        report = self._make_report()
        d = report.to_dict()
        expected_keys = {
            "generated_at",
            "current_versions_total",
            "versions_with_json_artifact",
            "versions_with_normalized_content",
            "json_derived_sections",
            "json_derived_fragments",
            "total_pair_evidence_rows",
            "total_matrix_cells",
            "active_model_version",
            "artifact_coverage",
            "evidence_state_counters",
            "sample_chains",
            "known_limitations",
        }
        assert expected_keys.issubset(d.keys())

    def test_to_dict_values_match(self):
        report = self._make_report(json_derived_sections=500, json_derived_fragments=1500)
        d = report.to_dict()
        assert d["json_derived_sections"] == 500
        assert d["json_derived_fragments"] == 1500

    def test_to_dict_artifact_coverage_rows(self):
        report = self._make_report(
            artifact_coverage=[
                ArtifactCoverageRow("json", 8, 80.0),
                ArtifactCoverageRow("html", 2, 20.0),
            ]
        )
        d = report.to_dict()
        assert len(d["artifact_coverage"]) == 2
        assert d["artifact_coverage"][0]["artifact_type"] == "json"
        assert d["artifact_coverage"][0]["pct_of_versions"] == 80.0

    def test_to_dict_evidence_state_counters(self):
        ec = EvidenceStateCountersOut(
            evidence_rows_present=2,
            healthy_empty_state=5,
            no_mnn=1,
        )
        report = self._make_report(evidence_state_counters=ec)
        d = report.to_dict()
        assert d["evidence_state_counters"]["evidence_rows_present"] == 2
        assert d["evidence_state_counters"]["healthy_empty_state"] == 5
        assert d["evidence_state_counters"]["no_mnn"] == 1

    def test_to_dict_sample_chains(self):
        chains = [
            SampleTraceabilityChain(
                version_id=1,
                section_id=10,
                fragment_id=100,
                source_artifact_type="json",
                source_block_id="b_0001",
                content_kind="text",
                fragment_text_preview="этот фрагмент содержит текст",
            )
        ]
        report = self._make_report(sample_chains=chains)
        d = report.to_dict()
        assert len(d["sample_chains"]) == 1
        assert d["sample_chains"][0]["source_artifact_type"] == "json"
        assert d["sample_chains"][0]["source_block_id"] == "b_0001"

    def test_to_markdown_contains_key_sections(self):
        ec = EvidenceStateCountersOut(healthy_empty_state=5)
        report = self._make_report(evidence_state_counters=ec)
        md = report.to_markdown()
        assert "Release Evidence Report" in md
        assert "Document Corpus" in md
        assert "Evidence State Distribution" in md
        assert "healthy_empty_state" in md
        assert "5" in md

    def test_to_markdown_artifact_coverage_section(self):
        report = self._make_report(
            artifact_coverage=[ArtifactCoverageRow("json", 8, 80.0)]
        )
        md = report.to_markdown()
        assert "Artifact Coverage" in md
        assert "json" in md
        assert "80.0%" in md

    def test_to_markdown_sample_chains_section(self):
        chains = [
            SampleTraceabilityChain(
                version_id=42,
                section_id=99,
                fragment_id=777,
                source_artifact_type="json",
                source_block_id="b_0042",
                content_kind="text",
                fragment_text_preview="sample fragment text",
            )
        ]
        report = self._make_report(sample_chains=chains)
        md = report.to_markdown()
        assert "Sample Traceability" in md
        assert "b_0042" in md
        assert "777" in md

    def test_to_markdown_known_limitations_section(self):
        report = self._make_report(
            known_limitations=["Limitation alpha", "Limitation beta"]
        )
        md = report.to_markdown()
        assert "Known Limitations" in md
        assert "Limitation alpha" in md
        assert "Limitation beta" in md

    def test_to_markdown_empty_active_model(self):
        """When active_model_version is None, markdown should not error."""
        report = self._make_report(active_model_version=None)
        md = report.to_markdown()
        assert "Release Evidence Report" in md

    def test_generated_at_is_utc(self):
        report = self._make_report()
        assert report.generated_at.tzinfo is not None


# ---- ReleaseEvidenceReportService unit tests ---------------------------------


class TestReleaseEvidenceReportService:
    """Unit tests with mocked DB session to avoid DB dependency."""

    def _make_mock_session(self):
        """Build a minimal mock session returning empty DB state."""
        session = MagicMock()
        # DocumentVersion query
        session.query.return_value.filter_by.return_value.all.return_value = []
        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.count.return_value = 0
        session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        return session

    def test_generate_report_empty_db_returns_zeros(self):
        mock_session = self._make_mock_session()
        svc = ReleaseEvidenceReportService()
        with patch("app.services.evidence_report.get_sync_session", return_value=mock_session), \
             patch.object(mock_session, "close"), \
             patch("app.services.evidence_report.EvidenceDiagnosticsService") as mock_diag:
            mock_diag.return_value.state_counters.return_value = EvidenceStateCountersOut()
            report = svc.generate_report(include_state_counters=False)

        assert report.current_versions_total == 0
        assert report.json_derived_sections == 0
        assert report.json_derived_fragments == 0
        assert report.total_pair_evidence_rows == 0

    def test_generate_report_returns_report_instance(self):
        mock_session = self._make_mock_session()
        svc = ReleaseEvidenceReportService()
        with patch("app.services.evidence_report.get_sync_session", return_value=mock_session), \
             patch.object(mock_session, "close"):
            report = svc.generate_report(include_state_counters=False)

        assert isinstance(report, ReleaseEvidenceReport)
        assert report.generated_at.tzinfo is not None

    def test_generate_report_has_known_limitations(self):
        mock_session = self._make_mock_session()
        svc = ReleaseEvidenceReportService()
        with patch("app.services.evidence_report.get_sync_session", return_value=mock_session), \
             patch.object(mock_session, "close"):
            report = svc.generate_report(include_state_counters=False)

        assert len(report.known_limitations) > 0
        assert any("MNN" in lim for lim in report.known_limitations)

    def test_generate_report_to_dict_and_markdown_are_consistent(self):
        mock_session = self._make_mock_session()
        svc = ReleaseEvidenceReportService()
        with patch("app.services.evidence_report.get_sync_session", return_value=mock_session), \
             patch.object(mock_session, "close"):
            report = svc.generate_report(include_state_counters=False)

        d = report.to_dict()
        md = report.to_markdown()
        assert isinstance(d, dict)
        assert isinstance(md, str)
        assert "Release Evidence Report" in md

    def test_generate_report_state_counters_failure_is_handled(self):
        """If EvidenceDiagnosticsService raises, report still returns valid object."""
        mock_session = self._make_mock_session()
        svc = ReleaseEvidenceReportService()
        with patch("app.services.evidence_report.get_sync_session", return_value=mock_session), \
             patch.object(mock_session, "close"), \
             patch("app.services.evidence_report.EvidenceDiagnosticsService") as mock_diag:
            mock_diag.return_value.state_counters.side_effect = RuntimeError("DB unavailable")
            report = svc.generate_report(include_state_counters=True)

        # Should still return a valid report with default (zero) counters
        assert isinstance(report, ReleaseEvidenceReport)
        assert report.evidence_state_counters.unknown == 0  # default

    def test_generate_report_without_state_counters(self):
        """include_state_counters=False should skip diagnostics service."""
        mock_session = self._make_mock_session()
        svc = ReleaseEvidenceReportService()
        with patch("app.services.evidence_report.get_sync_session", return_value=mock_session), \
             patch.object(mock_session, "close"), \
             patch("app.services.evidence_report.EvidenceDiagnosticsService") as mock_diag:
            svc.generate_report(include_state_counters=False)

        mock_diag.assert_not_called()

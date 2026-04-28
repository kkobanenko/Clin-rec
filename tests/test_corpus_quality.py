"""Unit tests for CorpusQualityService.

All tests use in-memory SQLite and mock get_sync_session.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.evidence import MatrixCell, PairEvidence
from app.models.scoring import ScoringModelVersion
from app.models.text import DocumentSection, TextFragment
from app.services.corpus_quality import (
    ContentKindBreakdown,
    CorpusQualityReport,
    CorpusQualityService,
    EvidenceRichnessReport,
)

# ── SQLite compat shims ────────────────────────────────────────────────────────


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(t, c, **kw):
    return "JSON"


@compiles(TSVECTOR, "sqlite")
def _tsvector_sqlite(t, c, **kw):
    return "TEXT"


# ── Fixtures ──────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)

ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def _recreate_schema():
    Base.metadata.create_all(ENGINE)
    yield
    Base.metadata.drop_all(ENGINE)


def _session():
    return Session()


def _setup_fragments(session, kinds: list[str]) -> list[TextFragment]:
    """Create DocumentRegistry → DocumentVersion → DocumentSection → N fragments."""
    reg = DocumentRegistry(title="Doc", discovered_at=_NOW)
    session.add(reg)
    session.flush()
    ver = DocumentVersion(registry_id=reg.id, version_hash="h1")
    session.add(ver)
    session.flush()
    sec = DocumentSection(
        document_version_id=ver.id, section_order=1, section_title="S1"
    )
    session.add(sec)
    session.flush()
    frags = []
    for i, kind in enumerate(kinds):
        f = TextFragment(
            section_id=sec.id,
            fragment_order=i,
            fragment_text=f"fragment {i}",
            content_kind=kind,
        )
        session.add(f)
        frags.append(f)
    session.flush()
    return frags


# ── ContentKindBreakdown tests ─────────────────────────────────────────────────


class TestContentKindBreakdown:
    def test_to_dict_keys(self):
        ck = ContentKindBreakdown(text=2, html=1, table_like=1, image=0, unknown=1, total=5)
        d = ck.to_dict()
        assert set(d.keys()) == {"text", "html", "table_like", "image", "unknown", "total"}
        assert d["total"] == 5

    def test_counts_correct(self):
        ck = ContentKindBreakdown(text=3, html=0, table_like=0, image=0, unknown=0, total=3)
        assert ck.to_dict()["text"] == 3


# ── EvidenceRichnessReport tests ───────────────────────────────────────────────


class TestEvidenceRichnessReport:
    def test_evidence_coverage_pct_zero_for_empty(self):
        r = EvidenceRichnessReport()
        assert r.evidence_coverage_pct == 0.0

    def test_evidence_coverage_pct_calculation(self):
        r = EvidenceRichnessReport(fragments_total=10, fragments_with_evidence=5)
        assert r.evidence_coverage_pct == 50.0

    def test_scoring_coverage_pct_zero_for_empty(self):
        r = EvidenceRichnessReport()
        assert r.scoring_coverage_pct == 0.0

    def test_scoring_coverage_pct_calculation(self):
        r = EvidenceRichnessReport(fragments_with_evidence=4, fragments_scored=3)
        assert r.scoring_coverage_pct == 75.0

    def test_to_dict_keys(self):
        r = EvidenceRichnessReport()
        d = r.to_dict()
        for key in (
            "fragments_total",
            "fragments_with_evidence",
            "fragments_scored",
            "pair_evidence_total",
            "pair_evidence_scored",
            "matrix_cell_total",
            "active_model_version_id",
            "evidence_coverage_pct",
            "scoring_coverage_pct",
        ):
            assert key in d


# ── CorpusQualityReport tests ─────────────────────────────────────────────────


class TestCorpusQualityReport:
    def test_to_dict_has_required_keys(self):
        report = CorpusQualityReport()
        d = report.to_dict()
        assert "overall_health" in d
        assert "content_kind" in d
        assert "richness" in d
        assert "flags" in d

    def test_to_markdown_contains_header(self):
        report = CorpusQualityReport()
        md = report.to_markdown()
        assert "# Corpus Quality Report" in md

    def test_to_markdown_contains_health(self):
        report = CorpusQualityReport(overall_health="healthy")
        md = report.to_markdown()
        assert "HEALTHY" in md

    def test_to_markdown_flags_section_only_when_flags_exist(self):
        report = CorpusQualityReport()
        md = report.to_markdown()
        assert "## Quality Flags" not in md

        from app.services.corpus_quality import CorpusQualityFlag

        report.flags.append(
            CorpusQualityFlag(
                severity="warn",
                metric="test_metric",
                value=0.1,
                threshold=0.5,
                message="test warning",
            )
        )
        md = report.to_markdown()
        assert "## Quality Flags" in md
        assert "test warning" in md


# ── CorpusQualityService integration-style tests ─────────────────────────────


class TestCorpusQualityServiceEmpty:
    def test_empty_corpus_returns_empty_health(self):
        session = _session()
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService()
            report = svc.generate_report()

        assert report.overall_health == "empty"
        assert report.content_kind.total == 0
        assert report.richness.fragments_total == 0


class TestCorpusQualityServiceWithFragments:
    def test_all_text_fragments_no_evidence(self):
        session = _session()
        _setup_fragments(session, ["text", "text", "text"])
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService()
            report = svc.generate_report()

        assert report.content_kind.text == 3
        assert report.content_kind.total == 3
        assert report.richness.fragments_total == 3
        assert report.richness.fragments_with_evidence == 0

    def test_mixed_content_kinds_counted(self):
        session = _session()
        _setup_fragments(session, ["text", "html", "image", "table_like", None])
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService()
            report = svc.generate_report()

        assert report.content_kind.text == 1
        assert report.content_kind.html == 1
        assert report.content_kind.image == 1
        assert report.content_kind.table_like == 1
        assert report.content_kind.unknown == 1
        assert report.content_kind.total == 5

    def test_image_heavy_corpus_raises_flag(self):
        session = _session()
        # 50% image → above 40% threshold
        _setup_fragments(session, ["image", "image", "text", "text"])
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService()
            report = svc.generate_report()

        flag_metrics = {f.metric for f in report.flags}
        assert "image_fraction" in flag_metrics

    def test_custom_threshold_suppresses_image_flag(self):
        session = _session()
        _setup_fragments(session, ["image", "image", "text", "text"])
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService(thresholds={"image_fraction_warn": 0.99})
            report = svc.generate_report()

        flag_metrics = {f.metric for f in report.flags}
        assert "image_fraction" not in flag_metrics

    def test_unknown_kind_heavy_raises_flag(self):
        session = _session()
        # 3/5 unknown = 60% → above 20% threshold
        _setup_fragments(session, [None, None, None, "text", "text"])
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService()
            report = svc.generate_report()

        flag_metrics = {f.metric for f in report.flags}
        assert "unknown_content_kind" in flag_metrics

    def test_overall_health_degraded_with_one_warning(self):
        session = _session()
        # Only image fragments → evidence_coverage=0 (no evidence → low coverage flag)
        # + image_fraction 100% → image flag → 2 flags → critical
        _setup_fragments(session, ["image", "image"])
        session.commit()

        with patch("app.services.corpus_quality.get_sync_session", return_value=session):
            svc = CorpusQualityService()
            report = svc.generate_report()

        # 2 flags: evidence_coverage + image_fraction
        assert report.overall_health in ("degraded", "critical")


class TestCorpusQualityServiceFlagDetails:
    def test_flag_to_dict_keys(self):
        from app.services.corpus_quality import CorpusQualityFlag

        flag = CorpusQualityFlag(
            severity="warn",
            metric="test",
            value=0.1,
            threshold=0.5,
            message="hello",
        )
        d = flag.to_dict()
        assert set(d.keys()) == {"severity", "metric", "value", "threshold", "message"}
        assert d["severity"] == "warn"

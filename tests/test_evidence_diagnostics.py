"""Tests for EvidenceDiagnosticsService — unit tests using SQLite."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.clinical import ClinicalContext
from app.models.document import DocumentRegistry, DocumentVersion, SourceArtifact
from app.models.evidence import PairEvidence
from app.models.molecule import Molecule
from app.models.pipeline_event import PipelineEventLog
from app.models.text import DocumentSection, TextFragment
from app.schemas.diagnostics import VersionEvidenceStateOut
from app.services.evidence_diagnostics import EvidenceDiagnosticsService, _bump_counter
from app.schemas.diagnostics import EvidenceStateCountersOut


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(t, c, **kw):
    return "JSON"


@compiles(TSVECTOR, "sqlite")
def _tsvector_sqlite(t, c, **kw):
    return "TEXT"


_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def diag_engine():
    engine = create_engine("sqlite:///test_evidence_diagnostics.db", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def diag_session(diag_engine):
    Session = sessionmaker(bind=diag_engine)
    sess = Session()
    try:
        yield sess
    finally:
        sess.rollback()
        sess.close()


def _make_version(session, *, registry_title="Test Doc", is_current=True):
    """Create a DocumentRegistry + DocumentVersion and return the version."""
    reg = DocumentRegistry(
        title=registry_title,
        discovered_at=_NOW,
        last_seen_at=_NOW,
    )
    session.add(reg)
    session.flush()
    ver = DocumentVersion(
        registry_id=reg.id,
        is_current=is_current,
        detected_at=_NOW,
    )
    session.add(ver)
    session.flush()
    return ver


def _make_fragment(session, *, section_id, text="hello world", content_kind="text", order=0):
    frag = TextFragment(
        section_id=section_id,
        fragment_order=order,
        fragment_type="paragraph",
        fragment_text=text,
        content_kind=content_kind,
    )
    session.add(frag)
    session.flush()
    return frag


def _make_section(session, *, version_id, title="Section 1", order=0):
    sec = DocumentSection(
        document_version_id=version_id,
        section_title=title,
        section_order=order,
    )
    session.add(sec)
    session.flush()
    return sec


# ---- Tests ---------------------------------------------------------------


class TestBumpCounter:
    def test_known_states_increment(self):
        counters = EvidenceStateCountersOut()
        _bump_counter(counters, "evidence_rows_present")
        assert counters.evidence_rows_present == 1
        _bump_counter(counters, "healthy_empty_state")
        assert counters.healthy_empty_state == 1
        _bump_counter(counters, "degraded_routing")
        assert counters.degraded_routing == 1
        _bump_counter(counters, "extraction_missing")
        assert counters.extraction_missing == 1
        _bump_counter(counters, "scoring_missing")
        assert counters.scoring_missing == 1
        _bump_counter(counters, "no_mnn")
        assert counters.no_mnn == 1

    def test_unknown_state_goes_to_unknown(self):
        counters = EvidenceStateCountersOut()
        _bump_counter(counters, "some_future_state")
        assert counters.unknown == 1

    def test_multiple_bumps_accumulate(self):
        counters = EvidenceStateCountersOut()
        for _ in range(5):
            _bump_counter(counters, "no_mnn")
        assert counters.no_mnn == 5


class TestEvidenceDiagnosticsServiceUnit:
    """Unit tests that patch get_sync_session and mock MNNExtractor."""

    def test_missing_version_returns_unknown(self):
        svc = EvidenceDiagnosticsService()
        with patch("app.services.evidence_diagnostics.get_sync_session") as mock_sess:
            mock_session = MagicMock()
            mock_session.get.return_value = None
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_sess.return_value = mock_session

            result = svc.diagnose_version(version_id=9999)
            assert result.dominant_evidence_state == "unknown"
            assert result.version_id == 9999

    def test_extraction_ran_check_uses_pipeline_event_log(self, diag_session):
        """_extraction_ran should query PipelineEventLog stage=extract status=success."""
        ver = _make_version(diag_session)
        # No events → not ran
        svc = EvidenceDiagnosticsService()
        assert svc._extraction_ran(diag_session, ver.id) is False

        # Add success event
        reg = diag_session.query(DocumentRegistry).get(ver.registry_id)
        evt = PipelineEventLog(
            document_registry_id=reg.id,
            document_version_id=ver.id,
            stage="extract",
            status="success",
            message="OK",
            created_at=_NOW,
        )
        diag_session.add(evt)
        diag_session.flush()
        assert svc._extraction_ran(diag_session, ver.id) is True

    def test_diagnose_version_extraction_missing(self, diag_session):
        """When no extraction event exists, dominant state is extraction_missing."""
        ver = _make_version(diag_session, registry_title="Extraction Missing Doc")
        sec = _make_section(diag_session, version_id=ver.id)
        _make_fragment(diag_session, section_id=sec.id)

        svc = EvidenceDiagnosticsService()
        # Patch to avoid actually calling sync_session (already opened above)
        with patch.object(svc, "_extraction_ran", return_value=False), \
             patch("app.services.evidence_diagnostics.get_sync_session", return_value=diag_session), \
             patch.object(diag_session, "close"):
            result = svc._diagnose_version_in_session(
                diag_session, ver.id, include_fragment_details=True
            )

        assert result.extraction_ran is False
        assert result.dominant_evidence_state == "extraction_missing"
        assert "extraction" in result.explanation.lower()

    def test_diagnose_version_degraded_routing(self, diag_session):
        """When majority of fragments are image kind, dominant state is degraded_routing."""
        ver = _make_version(diag_session, registry_title="Degraded Routing Doc")
        sec = _make_section(diag_session, version_id=ver.id)
        for i in range(4):
            _make_fragment(diag_session, section_id=sec.id, content_kind="image", order=i)
        _make_fragment(diag_session, section_id=sec.id, content_kind="text", order=10)

        mock_mnn = MagicMock()
        mock_mnn.extract.return_value = []
        svc = EvidenceDiagnosticsService()
        svc._mnn_extractor = mock_mnn

        with patch.object(svc, "_extraction_ran", return_value=True):
            result = svc._diagnose_version_in_session(
                diag_session, ver.id, include_fragment_details=True
            )

        assert result.fragments_ocr_unavailable == 4
        assert result.dominant_evidence_state == "degraded_routing"

    def test_diagnose_version_no_mnn(self, diag_session):
        """When extraction ran but MNN extractor finds nothing, state is no_mnn."""
        ver = _make_version(diag_session, registry_title="No MNN Doc")
        sec = _make_section(diag_session, version_id=ver.id)
        _make_fragment(diag_session, section_id=sec.id, text="plain text no drugs")

        mock_mnn = MagicMock()
        mock_mnn.extract.return_value = []
        svc = EvidenceDiagnosticsService()
        svc._mnn_extractor = mock_mnn

        with patch.object(svc, "_extraction_ran", return_value=True):
            result = svc._diagnose_version_in_session(
                diag_session, ver.id, include_fragment_details=True
            )

        assert result.dominant_evidence_state == "no_mnn"
        assert "0 MNN" in result.explanation or "zero MNN" in result.explanation.lower() or "found" in result.explanation.lower()

    def test_diagnose_version_healthy_empty(self, diag_session):
        """When fragments have MNN hits but no evidence rows, state is healthy_empty_state."""
        ver = _make_version(diag_session, registry_title="Healthy Empty Doc")
        sec = _make_section(diag_session, version_id=ver.id)
        _make_fragment(diag_session, section_id=sec.id, text="метопролол vs бисопролол")

        mock_mnn = MagicMock()
        mock_mnn.extract.return_value = [
            {"molecule_id": 1, "text": "метопролол"},
            {"molecule_id": 2, "text": "бисопролол"},
        ]
        svc = EvidenceDiagnosticsService()
        svc._mnn_extractor = mock_mnn

        with patch.object(svc, "_extraction_ran", return_value=True):
            result = svc._diagnose_version_in_session(
                diag_session, ver.id, include_fragment_details=True
            )

        assert result.dominant_evidence_state == "healthy_empty_state"
        assert result.fragments_with_mnn == 1
        assert result.pair_evidence_total == 0

    def test_fragment_diagnostics_included(self, diag_session):
        """Fragment diagnostics list is populated when include_fragment_details=True."""
        ver = _make_version(diag_session, registry_title="Fragment Details Doc")
        sec = _make_section(diag_session, version_id=ver.id)
        _make_fragment(diag_session, section_id=sec.id, text="some text")

        mock_mnn = MagicMock()
        mock_mnn.extract.return_value = []
        svc = EvidenceDiagnosticsService()
        svc._mnn_extractor = mock_mnn

        with patch.object(svc, "_extraction_ran", return_value=True):
            result = svc._diagnose_version_in_session(
                diag_session, ver.id, include_fragment_details=True
            )

        assert len(result.fragment_diagnostics) >= 1
        diag = result.fragment_diagnostics[0]
        assert diag.evidence_state in {
            "evidence_rows_present",
            "healthy_empty_state",
            "degraded_routing",
            "extraction_missing",
            "no_mnn",
        }

    def test_fragment_diagnostics_excluded(self, diag_session):
        """Fragment diagnostics list is empty when include_fragment_details=False."""
        ver = _make_version(diag_session, registry_title="No Fragment Details Doc")
        sec = _make_section(diag_session, version_id=ver.id)
        _make_fragment(diag_session, section_id=sec.id, text="some text")

        mock_mnn = MagicMock()
        mock_mnn.extract.return_value = []
        svc = EvidenceDiagnosticsService()
        svc._mnn_extractor = mock_mnn

        with patch.object(svc, "_extraction_ran", return_value=True):
            result = svc._diagnose_version_in_session(
                diag_session, ver.id, include_fragment_details=False
            )

        assert result.fragment_diagnostics == []

    def test_corpus_coverage_empty(self):
        """corpus_coverage returns zeros when there are no current versions."""
        svc = EvidenceDiagnosticsService()
        with patch("app.services.evidence_diagnostics.get_sync_session") as mock_sess_factory:
            mock_session = MagicMock()
            mock_session.query.return_value.filter_by.return_value.all.return_value = []
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            mock_sess_factory.return_value = mock_session

            result = svc.corpus_coverage()

        assert result.total_current_versions == 0
        assert result.coverage_pct == 0.0
        assert result.evidence_density_pct == 0.0

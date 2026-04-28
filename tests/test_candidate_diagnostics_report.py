"""Unit tests for CandidateDiagnosticsReportService."""

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
from app.models.pipeline_event import PipelineEventLog
from app.services.candidate_diagnostics_report import CandidateDiagnosticsReportService


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(_type, _compiler, **_kwargs):
    return "JSON"


@compiles(TSVECTOR, "sqlite")
def _tsvector_sqlite(_type, _compiler, **_kwargs):
    return "TEXT"


_NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Session = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def _recreate_schema():
    Base.metadata.create_all(ENGINE)
    yield
    Base.metadata.drop_all(ENGINE)


def _make_version(session, idx: int) -> DocumentVersion:
    reg = DocumentRegistry(
        title=f"Doc {idx}",
        external_id=f"DOC-{idx}",
        discovered_at=_NOW,
    )
    session.add(reg)
    session.flush()

    ver = DocumentVersion(registry_id=reg.id, version_hash=f"v-{idx}")
    session.add(ver)
    session.flush()
    return ver


def _make_extract_event(
    session,
    *,
    version: DocumentVersion,
    event_id: int,
    skip_rate: float,
    candidate_pairs_count: int,
    no_mnn: int = 0,
    single_mnn: int = 0,
    image: int = 0,
):
    event = PipelineEventLog(
        id=event_id,
        created_at=_NOW,
        document_registry_id=version.registry_id,
        document_version_id=version.id,
        stage="extract",
        status="success",
        message="ok",
        detail_json={
            "candidate_skip_rate": skip_rate,
            "candidate_pairs_count": candidate_pairs_count,
            "candidate_fragments_no_mnn": no_mnn,
            "candidate_fragments_single_mnn": single_mnn,
            "candidate_fragments_image": image,
            "version_score_contexts_count": 3,
        },
    )
    session.add(event)
    session.flush()


class TestCandidateDiagnosticsReportService:
    def test_empty_when_no_extract_events(self):
        session = Session()
        session.commit()

        with patch("app.services.candidate_diagnostics_report.get_sync_session", return_value=session):
            report = CandidateDiagnosticsReportService().generate_report()

        assert report.versions_considered == 0
        assert report.total_candidate_pairs == 0
        assert report.top_versions_by_skip_rate == []
        session.close()

    def test_aggregates_recent_extract_events(self):
        session = Session()
        version1 = _make_version(session, 1)
        version2 = _make_version(session, 2)
        version2_id = version2.id

        _make_extract_event(
            session,
            version=version1,
            event_id=1,
            skip_rate=0.25,
            candidate_pairs_count=8,
            no_mnn=2,
            single_mnn=1,
            image=0,
        )
        _make_extract_event(
            session,
            version=version2,
            event_id=2,
            skip_rate=0.9,
            candidate_pairs_count=0,
            no_mnn=7,
            single_mnn=3,
            image=2,
        )
        session.commit()

        with patch("app.services.candidate_diagnostics_report.get_sync_session", return_value=session):
            report = CandidateDiagnosticsReportService().generate_report(high_skip_threshold=0.8)

        assert report.versions_considered == 2
        assert report.versions_with_candidate_pairs == 1
        assert report.high_skip_versions == 1
        assert report.total_candidate_pairs == 8
        assert report.total_fragments_no_mnn == 9
        assert report.total_fragments_single_mnn == 4
        assert report.total_fragments_image == 2
        assert report.max_skip_rate == 0.9
        assert report.top_versions_by_skip_rate[0].document_version_id == version2_id
        session.close()

    def test_ignores_events_without_candidate_skip_rate(self):
        session = Session()
        version = _make_version(session, 1)

        event = PipelineEventLog(
            id=1,
            created_at=_NOW,
            document_registry_id=version.registry_id,
            document_version_id=version.id,
            stage="extract",
            status="success",
            message="ok",
            detail_json={"other_field": 1},
        )
        session.add(event)
        session.commit()

        with patch("app.services.candidate_diagnostics_report.get_sync_session", return_value=session):
            report = CandidateDiagnosticsReportService().generate_report()

        assert report.versions_considered == 0
        session.close()

    def test_markdown_contains_summary(self):
        session = Session()
        version = _make_version(session, 1)
        _make_extract_event(
            session,
            version=version,
            event_id=1,
            skip_rate=0.4,
            candidate_pairs_count=3,
            no_mnn=1,
            single_mnn=1,
            image=0,
        )
        session.commit()

        with patch("app.services.candidate_diagnostics_report.get_sync_session", return_value=session):
            report = CandidateDiagnosticsReportService().generate_report()

        markdown = report.to_markdown()
        assert "# Candidate Diagnostics Report" in markdown
        assert "Versions considered" in markdown
        assert "Top Versions By Skip Rate" in markdown
        session.close()

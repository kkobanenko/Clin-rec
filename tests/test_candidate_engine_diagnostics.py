"""Unit tests for CandidateEngine.generate_pairs_with_diagnostics and related types.

Uses an in-memory SQLite database — same setup pattern as other unit-test modules.
All MNN/relation/UUR-UDD extractors are mocked to avoid DB calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from itertools import permutations
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.clinical import ClinicalContext
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.evidence import PairEvidence
from app.models.molecule import Molecule
from app.models.text import DocumentSection, TextFragment
from app.services.candidate_engine import (
    CandidateDiagnosticResult,
    CandidateEngine,
    FragmentCandidateDiagnostic,
    FragmentSkipReason,
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


def _make_registry(session) -> DocumentRegistry:
    reg = DocumentRegistry(
        title="Test Document",
        external_id="DOC-001",
        discovered_at=_NOW,
    )
    session.add(reg)
    session.flush()
    return reg


def _make_version(session, registry_id: int) -> DocumentVersion:
    ver = DocumentVersion(registry_id=registry_id, version_hash="abc123")
    session.add(ver)
    session.flush()
    return ver


def _make_context(session, version_id: int) -> ClinicalContext:
    ctx = ClinicalContext(
        document_version_id=version_id,
        disease_name="Test disease",
        context_signature=f"sig_{version_id}",
    )
    session.add(ctx)
    session.flush()
    return ctx


def _make_molecule(session, name: str) -> Molecule:
    mol = Molecule(inn_ru=name)
    session.add(mol)
    session.flush()
    return mol


def _make_section(session, version_id: int) -> DocumentSection:
    sec = DocumentSection(
        document_version_id=version_id,
        section_order=1,
        section_title="Test section",
    )
    session.add(sec)
    session.flush()
    return sec


def _make_fragment(
    session,
    section_id: int,
    text: str,
    content_kind: str = "text",
    order: int = 1,
) -> TextFragment:
    frag = TextFragment(
        section_id=section_id,
        fragment_order=order,
        fragment_text=text,
        content_kind=content_kind,
    )
    session.add(frag)
    session.flush()
    return frag


# ── Dataclass tests ────────────────────────────────────────────────────────────


class TestCandidateDiagnosticResult:
    def test_total_fragments_processed(self):
        result = CandidateDiagnosticResult(version_id=1)
        result.fragment_diagnostics = [
            FragmentCandidateDiagnostic(
                fragment_id=i,
                fragment_text_prefix="",
                content_kind="text",
                mnn_hits=0,
                new_pairs=0,
                skipped_pairs=0,
                skip_reason=FragmentSkipReason.NO_MNN,
            )
            for i in range(3)
        ]
        assert result.total_fragments_processed == 3

    def test_skip_rate_zero_when_all_productive(self):
        result = CandidateDiagnosticResult(version_id=1, fragments_with_pairs=4)
        result.fragment_diagnostics = [
            FragmentCandidateDiagnostic(
                fragment_id=i,
                fragment_text_prefix="",
                content_kind="text",
                mnn_hits=2,
                new_pairs=1,
                skipped_pairs=0,
                skip_reason=FragmentSkipReason.PRODUCED_PAIRS,
            )
            for i in range(4)
        ]
        assert result.skip_rate == 0.0

    def test_skip_rate_one_when_none_productive(self):
        result = CandidateDiagnosticResult(version_id=1, fragments_with_pairs=0)
        result.fragment_diagnostics = [
            FragmentCandidateDiagnostic(
                fragment_id=i,
                fragment_text_prefix="",
                content_kind="text",
                mnn_hits=0,
                new_pairs=0,
                skipped_pairs=0,
                skip_reason=FragmentSkipReason.NO_MNN,
            )
            for i in range(2)
        ]
        assert result.skip_rate == 1.0

    def test_skip_rate_zero_when_no_fragments(self):
        result = CandidateDiagnosticResult(version_id=1)
        assert result.skip_rate == 0.0

    def test_to_dict_keys(self):
        result = CandidateDiagnosticResult(version_id=42)
        d = result.to_dict()
        assert d["version_id"] == 42
        for key in (
            "total_new_pairs",
            "total_skipped_pairs",
            "fragments_with_pairs",
            "fragments_single_mnn",
            "fragments_no_mnn",
            "fragments_image",
            "fragments_all_exist",
            "total_fragments_processed",
            "skip_rate",
            "fragment_diagnostics",
        ):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_fragment_diagnostics_serialised(self):
        result = CandidateDiagnosticResult(version_id=1)
        result.fragment_diagnostics = [
            FragmentCandidateDiagnostic(
                fragment_id=99,
                fragment_text_prefix="hello",
                content_kind="html",
                mnn_hits=3,
                new_pairs=2,
                skipped_pairs=1,
                skip_reason=FragmentSkipReason.PRODUCED_PAIRS,
                context_id=5,
            )
        ]
        d = result.to_dict()
        fdiag = d["fragment_diagnostics"][0]
        assert fdiag["fragment_id"] == 99
        assert fdiag["content_kind"] == "html"
        assert fdiag["mnn_hits"] == 3
        assert fdiag["skip_reason"] == "produced_pairs"
        assert fdiag["context_id"] == 5


class TestFragmentSkipReason:
    def test_all_enum_values_are_strings(self):
        for reason in FragmentSkipReason:
            assert isinstance(reason.value, str)

    def test_skip_reason_values(self):
        assert FragmentSkipReason.NO_CONTEXT.value == "no_context"
        assert FragmentSkipReason.SINGLE_MNN.value == "single_mnn"
        assert FragmentSkipReason.NO_MNN.value == "no_mnn"
        assert FragmentSkipReason.ALL_PAIRS_EXIST.value == "all_pairs_exist"
        assert FragmentSkipReason.IMAGE_FRAGMENT.value == "image_fragment"
        assert FragmentSkipReason.PRODUCED_PAIRS.value == "produced_pairs"


# ── Engine.generate_pairs_with_diagnostics tests ──────────────────────────────


def _mock_engine() -> CandidateEngine:
    """Return a CandidateEngine with all extractors mocked."""
    engine = CandidateEngine.__new__(CandidateEngine)
    engine.mnn_extractor = MagicMock()
    engine.relation_extractor = MagicMock()
    engine.uur_udd_extractor = MagicMock()
    # Reasonable defaults
    engine.mnn_extractor.load_dictionary.return_value = None
    engine.relation_extractor.extract.return_value = []
    engine.relation_extractor.classify_relation.return_value = ("inhibition", 0.8)
    engine.uur_udd_extractor.extract.return_value = []
    return engine


class TestGeneratePairsWithDiagnostics:
    def test_no_contexts_returns_empty_result(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        session.commit()

        engine = _mock_engine()
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(version_id=ver.id)

        assert result.total_new_pairs == 0
        assert result.total_fragments_processed == 0
        session.close()

    def test_image_fragment_is_skipped(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        _make_context(session, ver.id)
        sec = _make_section(session, ver.id)
        _make_fragment(session, sec.id, "image data", content_kind="image")
        session.commit()

        engine = _mock_engine()
        # MNN extractor should NOT be called for image fragments
        engine.mnn_extractor.extract.return_value = [
            {"molecule_id": 1}, {"molecule_id": 2}
        ]
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(version_id=ver.id)

        assert result.total_new_pairs == 0
        assert result.fragments_image == 1
        assert result.fragment_diagnostics[0].skip_reason == FragmentSkipReason.IMAGE_FRAGMENT
        session.close()

    def test_no_mnn_hits_fragment(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        _make_context(session, ver.id)
        sec = _make_section(session, ver.id)
        _make_fragment(session, sec.id, "no drugs here", content_kind="text")
        session.commit()

        engine = _mock_engine()
        engine.mnn_extractor.extract.return_value = []
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(version_id=ver.id)

        assert result.total_new_pairs == 0
        assert result.fragments_no_mnn == 1
        assert result.fragment_diagnostics[0].skip_reason == FragmentSkipReason.NO_MNN
        session.close()

    def test_single_mnn_hit_fragment(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        _make_context(session, ver.id)
        sec = _make_section(session, ver.id)
        _make_fragment(session, sec.id, "only aspirin present", content_kind="text")
        session.commit()

        engine = _mock_engine()
        engine.mnn_extractor.extract.return_value = [{"molecule_id": 1}]
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(version_id=ver.id)

        assert result.total_new_pairs == 0
        assert result.fragments_single_mnn == 1
        assert result.fragment_diagnostics[0].skip_reason == FragmentSkipReason.SINGLE_MNN
        session.close()

    def test_two_mnn_hits_creates_two_pairs(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        mol_a = _make_molecule(session, "DrugA")
        mol_b = _make_molecule(session, "DrugB")
        _make_context(session, ver.id)
        sec = _make_section(session, ver.id)
        _make_fragment(session, sec.id, "DrugA and DrugB interact", content_kind="text")
        session.commit()
        # Capture IDs before session is closed by the service
        mol_a_id, mol_b_id, ver_id = mol_a.id, mol_b.id, ver.id

        engine = _mock_engine()
        engine.mnn_extractor.extract.return_value = [
            {"molecule_id": mol_a_id},
            {"molecule_id": mol_b_id},
        ]
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(version_id=ver_id)

        # A→B and B→A
        assert result.total_new_pairs == 2
        assert result.fragments_with_pairs == 1
        assert result.fragment_diagnostics[0].skip_reason == FragmentSkipReason.PRODUCED_PAIRS

        fresh = Session()
        pairs = fresh.query(PairEvidence).all()
        assert len(pairs) == 2
        pair_directions = {(p.molecule_from_id, p.molecule_to_id) for p in pairs}
        assert (mol_a_id, mol_b_id) in pair_directions
        assert (mol_b_id, mol_a_id) in pair_directions
        fresh.close()

    def test_existing_pairs_are_skipped(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        mol_a = _make_molecule(session, "DrugA")
        mol_b = _make_molecule(session, "DrugB")
        ctx = _make_context(session, ver.id)
        sec = _make_section(session, ver.id)
        frag = _make_fragment(session, sec.id, "DrugA and DrugB", content_kind="text")
        # Pre-insert the A→B pair
        session.add(
            PairEvidence(
                context_id=ctx.id,
                molecule_from_id=mol_a.id,
                molecule_to_id=mol_b.id,
                fragment_id=frag.id,
                relation_type="inhibition",
                review_status="auto",
                extractor_version="test",
            )
        )
        session.commit()

        engine = _mock_engine()
        engine.mnn_extractor.extract.return_value = [
            {"molecule_id": mol_a.id},
            {"molecule_id": mol_b.id},
        ]
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(version_id=ver.id)

        # B→A is new, A→B is skipped
        assert result.total_new_pairs == 1
        assert result.total_skipped_pairs == 1
        session.close()

    def test_max_fragment_details_limit(self):
        session = Session()
        reg = _make_registry(session)
        ver = _make_version(session, reg.id)
        _make_context(session, ver.id)
        sec = _make_section(session, ver.id)
        # Add 5 fragments — all with no MNN
        for i in range(5):
            _make_fragment(session, sec.id, f"fragment {i}", content_kind="text", order=i)
        session.commit()

        engine = _mock_engine()
        engine.mnn_extractor.extract.return_value = []
        with patch("app.services.candidate_engine.get_sync_session", return_value=session):
            result = engine.generate_pairs_with_diagnostics(
                version_id=ver.id,
                max_fragment_details=3,
            )

        # Should still count all 5 in totals but only store 3 in fragment_diagnostics
        assert result.fragments_no_mnn == 5
        assert len(result.fragment_diagnostics) == 3
        session.close()

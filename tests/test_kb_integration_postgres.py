"""
Интеграция KB с реальным Postgres: миграции Alembic, compile, lint, FTS.

Запуск (пример, как в docker-compose):
  CRIN_INTEGRATION_POSTGRES_URL=postgresql://crplatform:crplatform@127.0.0.1:5433/crplatform \\
  pytest tests/test_kb_integration_postgres.py -v
"""

from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

from app.core import sync_database
from app.models.clinical import ClinicalContext
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.evidence import PairEvidence
from app.models.knowledge import KnowledgeArtifact
from app.models.molecule import Molecule
from app.models.text import DocumentSection, TextFragment
from app.services.candidate_engine import CandidateEngine
from app.services.extraction.pipeline import ExtractionPipeline
from app.services.index_stats import refresh_knowledge_artifact_fts
from app.services.knowledge_compile import KnowledgeCompileService
from app.services.knowledge_lint import KnowledgeLintService

PG_URL = os.environ.get("CRIN_INTEGRATION_POSTGRES_URL")


@pytest.fixture(scope="module")
def pg_engine():
    if not PG_URL:
        pytest.skip("Задайте CRIN_INTEGRATION_POSTGRES_URL для интеграционного теста Postgres")
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", PG_URL)
    command.upgrade(cfg, "head")
    eng = create_engine(PG_URL, pool_pre_ping=True)
    yield eng
    eng.dispose()


def test_kb_compile_lint_fts(pg_engine, monkeypatch):
    """Цепочка: document → compile_version → типы 12.3 → lint → обновление search_vector."""
    Session = sessionmaker(bind=pg_engine)

    # Подменяем sync session в сервисах, чтобы использовать тот же engine без отдельного CRIN_ env.
    def open_session():
        s = Session()
        monkeypatch.setattr(s, "close", lambda: None)
        return s

    monkeypatch.setattr("app.services.knowledge_compile.get_sync_session", open_session)
    monkeypatch.setattr("app.services.knowledge_lint.get_sync_session", open_session)

    seed = Session()
    ext = "integration-kb-test-doc"
    seed.execute(delete(DocumentRegistry).where(DocumentRegistry.external_id == ext))
    seed.commit()
    reg = DocumentRegistry(external_id=ext, title="Интеграционный документ КР", card_url="http://example/card")
    seed.add(reg)
    seed.flush()
    ver = DocumentVersion(
        registry_id=reg.id,
        version_hash="integration-hash",
        source_type_primary="html",
        is_current=True,
    )
    seed.add(ver)
    seed.commit()
    vid = int(ver.id)
    seed.close()

    out = KnowledgeCompileService().compile_version(vid)
    assert out["status"] == "ok"

    check = Session()
    try:
        types = {r[0] for r in check.query(KnowledgeArtifact.artifact_type).distinct()}
        assert "source_digest" in types
        assert "entity_page" in types
        assert "glossary_term" in types
        assert "open_question" in types
        assert "master_index" in types
    finally:
        check.close()

    lint_out = KnowledgeLintService().run()
    assert lint_out["status"] == "ok"
    assert "conflict_groups_distinct" in lint_out

    monkeypatch.setattr("app.services.index_stats.sync_engine", pg_engine)

    def fts_session():
        s = Session()
        monkeypatch.setattr(s, "close", lambda: None)
        return s

    monkeypatch.setattr("app.services.index_stats.get_sync_session", fts_session)
    fts_out = refresh_knowledge_artifact_fts()
    assert fts_out.get("fts_skipped") is False, fts_out
    assert fts_out.get("fts_rows_updated", 0) >= 1


def _cleanup_pair_evidence_fixture(session, external_id: str) -> None:
    """Удаляем pair_evidence и документ с цепочкой, чтобы тест был идемпотентным."""
    reg_ids = list(session.execute(select(DocumentRegistry.id).where(DocumentRegistry.external_id == external_id)).scalars())
    for rid in reg_ids:
        vids = list(
            session.execute(select(DocumentVersion.id).where(DocumentVersion.registry_id == rid)).scalars()
        )
        for vid in vids:
            frag_ids = list(
                session.execute(
                    select(TextFragment.id)
                    .join(DocumentSection, DocumentSection.id == TextFragment.section_id)
                    .where(DocumentSection.document_version_id == vid)
                ).scalars()
            )
            if frag_ids:
                session.execute(delete(PairEvidence).where(PairEvidence.fragment_id.in_(frag_ids)))
            session.execute(delete(ClinicalContext).where(ClinicalContext.document_version_id == vid))
        session.execute(delete(DocumentRegistry).where(DocumentRegistry.id == rid))
    session.execute(
        delete(Molecule).where(
            Molecule.inn_ru.in_(["инттестместныйметотрексат", "инттестместныйлефлуномид"])
        )
    )
    session.commit()


def test_extract_creates_pair_evidence(pg_engine, monkeypatch):
    """TZ §14→§15: extract + CandidateEngine создаёт PairEvidence при ≥2 МНН во фрагменте."""
    Session = sessionmaker(bind=pg_engine)

    def open_session():
        s = Session()
        monkeypatch.setattr(s, "close", lambda: None)
        return s

    monkeypatch.setattr(sync_database, "get_sync_session", open_session)

    seed = Session()
    ext = "integration-pair-evidence-doc"
    _cleanup_pair_evidence_fixture(seed, ext)
    seed.add_all(
        [
            Molecule(inn_ru="инттестместныйметотрексат", inn_en=None),
            Molecule(inn_ru="инттестместныйлефлуномид", inn_en=None),
        ]
    )
    seed.commit()

    reg = DocumentRegistry(
        external_id=ext,
        title="Клинические рекомендации: Ревматоидный артрит",
        card_url="http://example/card",
    )
    seed.add(reg)
    seed.flush()
    ver = DocumentVersion(
        registry_id=reg.id,
        version_hash="pair-test-hash",
        source_type_primary="html",
        is_current=True,
    )
    seed.add(ver)
    seed.flush()
    sec = DocumentSection(document_version_id=ver.id, section_order=0, section_title="Терапия")
    seed.add(sec)
    seed.flush()
    frag = TextFragment(
        section_id=sec.id,
        fragment_order=0,
        fragment_text="Инттестместныйметотрексат или инттестместныйлефлуномид.",
    )
    seed.add(frag)
    seed.commit()
    vid = int(ver.id)
    seed.close()

    ExtractionPipeline().extract(vid)
    n = CandidateEngine().generate_pairs(vid)
    assert n >= 1

    check = Session()
    try:
        cnt = check.query(PairEvidence).count()
        assert cnt >= 1
    finally:
        check.close()
        clean = Session()
        _cleanup_pair_evidence_fixture(clean, ext)
        clean.close()

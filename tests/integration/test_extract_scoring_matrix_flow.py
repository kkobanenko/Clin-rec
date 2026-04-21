from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.models.clinical import ClinicalContext
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.evidence import MatrixCell, PairContextScore, PairEvidence
from app.models.molecule import Molecule
from app.models.scoring import ScoringModelVersion
from app.models.text import DocumentSection, TextFragment
from app.workers.tasks.extract import extract_document


def _clear_scoring_tables(session):
    session.query(MatrixCell).delete()
    session.query(PairContextScore).delete()
    session.query(PairEvidence).delete()
    session.query(ClinicalContext).delete()
    session.query(DocumentSection).delete()
    session.query(TextFragment).delete()
    session.query(DocumentVersion).delete()
    session.query(DocumentRegistry).delete()
    session.query(ScoringModelVersion).delete()
    session.query(Molecule).filter(
        Molecule.inn_ru.in_(["инттестскорметотрексат", "инттестскорлефлуномид"])
    ).delete(synchronize_session=False)
    session.commit()


def test_extract_task_builds_scores_and_matrix_when_active_model_exists(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)
    emitted_events: list[dict] = []

    monkeypatch.setattr("app.workers.tasks.extract.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.extraction.pipeline.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.candidate_engine.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.extraction.mnn_extractor.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.scoring.engine.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.matrix_builder.get_sync_session", lambda: session_factory())
    monkeypatch.setattr(
        "app.workers.tasks.extract.write_pipeline_event",
        lambda **kwargs: emitted_events.append(kwargs),
    )

    setup_session = session_factory()
    _clear_scoring_tables(setup_session)
    setup_session.add_all(
        [
            Molecule(inn_ru="инттестскорметотрексат", inn_en=None),
            Molecule(inn_ru="инттестскорлефлуномид", inn_en=None),
        ]
    )
    setup_session.add(
        ScoringModelVersion(
            version_label="integration-active-model",
            weights_json={"role": 0.2, "text": 0.25, "population": 0.15, "parity": 0.15, "practical": 0.1, "penalty": 0.15},
            description="integration active model",
            is_active=True,
        )
    )
    setup_session.commit()

    registry = DocumentRegistry(
        external_id="extract-score-matrix-test-doc",
        title="Клинические рекомендации: Ревматоидный артрит",
        discovered_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    setup_session.add(registry)
    setup_session.flush()
    version = DocumentVersion(
        registry_id=registry.id,
        version_hash="extract-score-matrix-hash",
        source_type_primary="html",
        source_type_available="html",
        is_current=True,
    )
    setup_session.add(version)
    setup_session.flush()
    section = DocumentSection(document_version_id=version.id, section_order=0, section_title="Терапия первой линии")
    setup_session.add(section)
    setup_session.flush()
    setup_session.add(
        TextFragment(
            section_id=section.id,
            fragment_order=0,
            fragment_text="Первая линия терапии: инттестскорметотрексат или инттестскорлефлуномид. УУР A, УДД 1.",
        )
    )
    setup_session.commit()
    version_id = version.id
    setup_session.close()

    extract_document(version_id)

    verify_session = session_factory()
    pair_evidence = verify_session.query(PairEvidence).all()
    pair_scores = verify_session.query(PairContextScore).all()
    matrix_cells = verify_session.query(MatrixCell).all()

    assert len(pair_evidence) >= 2
    assert len(pair_scores) >= 2
    assert len(matrix_cells) >= 2
    assert emitted_events[-1]["status"] == "success"
    assert emitted_events[-1]["detail_json"]["active_model_version_id"] is not None
    assert emitted_events[-1]["detail_json"]["score_contexts_count"] >= 2
    assert emitted_events[-1]["detail_json"]["matrix_cells_count"] >= 2

    _clear_scoring_tables(verify_session)
    verify_session.close()
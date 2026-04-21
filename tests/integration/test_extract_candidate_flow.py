from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from app.models.clinical import ClinicalContext
from app.models.document import DocumentRegistry, DocumentVersion
from app.models.evidence import PairEvidence
from app.models.molecule import Molecule
from app.models.text import DocumentSection, TextFragment
from app.workers.tasks.extract import extract_document


def _clear_extract_tables(session):
    session.query(PairEvidence).delete()
    session.query(ClinicalContext).delete()
    session.query(TextFragment).delete()
    session.query(DocumentSection).delete()
    session.query(DocumentVersion).delete()
    session.query(DocumentRegistry).delete()
    session.query(Molecule).filter(
        Molecule.inn_ru.in_(["инттестметотрексат", "инттестлефлуномид"])
    ).delete(synchronize_session=False)
    session.commit()


def test_extract_task_generates_candidate_pairs_and_event_stats(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)
    emitted_events: list[dict] = []

    monkeypatch.setattr("app.workers.tasks.extract.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.extraction.pipeline.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.candidate_engine.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.extraction.mnn_extractor.get_sync_session", lambda: session_factory())
    monkeypatch.setattr(
        "app.workers.tasks.extract.write_pipeline_event",
        lambda **kwargs: emitted_events.append(kwargs),
    )

    setup_session = session_factory()
    _clear_extract_tables(setup_session)
    setup_session.add_all(
        [
            Molecule(inn_ru="инттестметотрексат", inn_en=None),
            Molecule(inn_ru="инттестлефлуномид", inn_en=None),
        ]
    )
    setup_session.commit()

    registry = DocumentRegistry(
        external_id="extract-candidate-test-doc",
        title="Клинические рекомендации: Ревматоидный артрит",
        discovered_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    setup_session.add(registry)
    setup_session.flush()
    version = DocumentVersion(
        registry_id=registry.id,
        version_hash="extract-candidate-hash",
        source_type_primary="html",
        source_type_available="html",
        is_current=True,
    )
    setup_session.add(version)
    setup_session.flush()
    section = DocumentSection(
        document_version_id=version.id,
        section_order=0,
        section_title="Терапия первой линии",
    )
    setup_session.add(section)
    setup_session.flush()
    setup_session.add(
        TextFragment(
            section_id=section.id,
            fragment_order=0,
            fragment_text=(
                "Первая линия терапии: инттестметотрексат или инттестлефлуномид. "
                "УУР A, УДД 1."
            ),
        )
    )
    setup_session.commit()
    version_id = version.id
    setup_session.close()

    extract_document(version_id)

    verify_session = session_factory()
    contexts = verify_session.query(ClinicalContext).filter_by(document_version_id=version_id).all()
    pair_evidence = verify_session.query(PairEvidence).all()

    assert len(contexts) >= 1
    assert len(pair_evidence) >= 2
    assert emitted_events[0]["stage"] == "extract"
    assert emitted_events[0]["status"] == "start"
    assert emitted_events[-1]["stage"] == "extract"
    assert emitted_events[-1]["status"] == "success"
    assert emitted_events[-1]["detail_json"]["context_count"] >= 1
    assert emitted_events[-1]["detail_json"]["mnn_count"] >= 2
    assert emitted_events[-1]["detail_json"]["candidate_pairs_count"] >= 2

    _clear_extract_tables(verify_session)
    verify_session.close()
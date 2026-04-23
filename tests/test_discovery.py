from sqlalchemy.orm import sessionmaker

from app.models.pipeline import PipelineRun
from app.services.discovery import DiscoveryService


def test_discovery_execute_applies_limit_and_tracks_failed_count(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)

    monkeypatch.setattr("app.services.discovery.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.discovery.settings.discovery_max_records", 3)
    monkeypatch.setattr(
        DiscoveryService,
        "_discover_documents",
        lambda self: (
            [
                {"external_id": "doc-1", "title": "Doc 1"},
                {"external_id": "doc-2", "title": "Doc 2"},
                {"external_id": "doc-2", "title": "Doc 2 duplicate"},
                {"external_id": "", "title": "Missing id"},
                {"external_id": "doc-3", "title": "Doc 3"},
            ],
            {"strategy": "unit-test"},
        ),
    )
    monkeypatch.setattr(DiscoveryService, "_get_probe_candidates", lambda self, session, mode: [])

    setup_session = session_factory()
    run = PipelineRun(stage="discovery", run_type="full", status="pending")
    setup_session.add(run)
    setup_session.commit()
    run_id = run.id
    setup_session.close()

    DiscoveryService().execute(run_id, mode="full")

    verify_session = session_factory()
    stored_run = verify_session.get(PipelineRun, run_id)

    assert stored_run is not None
    assert stored_run.status == "completed"
    assert stored_run.discovered_count == 3
    assert stored_run.fetched_count == 2
    assert stored_run.parsed_count == 2
    assert stored_run.failed_count == 1
    assert stored_run.stats_json["total_raw_records"] == 5
    assert stored_run.stats_json["duplicates_detected"] == 1
    assert stored_run.stats_json["skipped_no_external_id"] == 1
    assert stored_run.stats_json["coverage_percent"] == 66.7

    verify_session.close()


def test_discovery_execute_does_not_limit_incremental_mode(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)

    monkeypatch.setattr("app.services.discovery.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.discovery.settings.discovery_max_records", 1)
    monkeypatch.setattr(
        DiscoveryService,
        "_discover_documents",
        lambda self: (
            [
                {"external_id": "doc-a", "title": "Doc A"},
                {"external_id": "doc-b", "title": "Doc B"},
            ],
            {"strategy": "unit-test"},
        ),
    )
    monkeypatch.setattr(DiscoveryService, "_get_probe_candidates", lambda self, session, mode: [])

    setup_session = session_factory()
    run = PipelineRun(stage="discovery", run_type="incremental", status="pending")
    setup_session.add(run)
    setup_session.commit()
    run_id = run.id
    setup_session.close()

    DiscoveryService().execute(run_id, mode="incremental")

    verify_session = session_factory()
    stored_run = verify_session.get(PipelineRun, run_id)

    assert stored_run is not None
    assert stored_run.discovered_count == 2
    assert stored_run.fetched_count == 2
    assert stored_run.parsed_count == 2
    assert stored_run.failed_count == 0

    verify_session.close()
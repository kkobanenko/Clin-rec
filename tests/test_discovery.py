import httpx
from sqlalchemy.orm import sessionmaker

from app.models.pipeline import PipelineRun
from app.services.discovery import DiscoveryService


def test_discovery_execute_applies_limit_and_tracks_failed_count(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)

    monkeypatch.setattr("app.services.discovery.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.discovery.settings.discovery_mode", "smoke")
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
    monkeypatch.setattr("app.services.discovery.settings.discovery_mode", "smoke")
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


def test_discovery_strategy_report_present_and_counts(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)

    monkeypatch.setattr("app.services.discovery.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.discovery.settings.discovery_mode", "smoke")
    monkeypatch.setattr("app.services.discovery.settings.discovery_max_records", 5)
    monkeypatch.setattr(
        DiscoveryService,
        "_discover_documents",
        lambda self: (
            [
                {"external_id": "doc-a", "title": "A"},
                {"external_id": "", "title": "No ID"},
                {"external_id": "doc-b", "title": "B"},
            ],
            {
                "strategy": "backend_api",
                "api_attempted": True,
                "api_status": "success",
                "api_records": 2,
                "dom_attempted": False,
                "dom_records": 0,
                "fallback_attempted": False,
                "fallback_reason": None,
            },
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

    report = stored_run.stats_json.get("discovery_strategy_report")
    assert report is not None
    assert report["strategy_used"] == "backend_api"
    assert report["strategy"] == "backend_api"
    assert report["mode"] == "smoke"
    assert report["attempted"] is True
    assert report["api_attempted"] is True
    assert report["api_status"] == "success"
    assert report["records_with_external_id"] == 2
    assert report["records_without_external_id"] == 1
    assert report["completeness_mode"] == "smoke"
    assert report["completeness_claim"] == "smoke_only"

    verify_session.close()


def test_discovery_corpus_mode_disables_limit(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)

    monkeypatch.setattr("app.services.discovery.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.discovery.settings.discovery_mode", "corpus")
    monkeypatch.setattr("app.services.discovery.settings.discovery_max_records", 1)
    monkeypatch.setattr(
        DiscoveryService,
        "_discover_documents",
        lambda self: (
            [
                {"external_id": "doc-1", "title": "1"},
                {"external_id": "doc-2", "title": "2"},
                {"external_id": "doc-3", "title": "3"},
            ],
            {
                "strategy": "backend_api",
                "api_attempted": True,
                "api_status": "success",
                "api_records": 3,
                "dom_attempted": False,
                "dom_records": 0,
                "fallback_attempted": False,
                "fallback_reason": None,
            },
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

    report = stored_run.stats_json.get("discovery_strategy_report")
    assert stored_run.discovered_count == 3
    assert report["completeness_mode"] == "corpus"
    assert report["mode"] == "corpus"
    assert report["limit_applied"] is False
    assert report["completeness_claim"] == "full_corpus_unverified"

    verify_session.close()


def test_discovery_corpus_mode_with_fallback_reports_partial(sync_engine, monkeypatch):
    session_factory = sessionmaker(bind=sync_engine)

    monkeypatch.setattr("app.services.discovery.get_sync_session", lambda: session_factory())
    monkeypatch.setattr("app.services.discovery.settings.discovery_mode", "corpus")
    monkeypatch.setattr(
        DiscoveryService,
        "_discover_documents",
        lambda self: (
            [
                {"external_id": "doc-1", "title": "Doc 1"},
            ],
            {
                "strategy": "playwright_fallback",
                "api_attempted": True,
                "api_status": "451",
                "api_records": 0,
                "dom_attempted": True,
                "dom_records": 1,
                "fallback_attempted": True,
                "fallback_reason": "api_451",
            },
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
    report = stored_run.stats_json.get("discovery_strategy_report")

    assert report["mode"] == "corpus"
    assert report["fallback_used"] is True
    assert report["completeness_claim"] == "partial_corpus"

    verify_session.close()


def test_discovery_backend_api_451_sets_fallback_reason(monkeypatch):
    class _Resp:
        status_code = 451

    class _Client:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, *args, **kwargs):
            req = httpx.Request("POST", "https://example.invalid")
            resp = httpx.Response(451, request=req)
            raise httpx.HTTPStatusError("451", request=req, response=resp)

    monkeypatch.setattr("app.services.discovery.httpx.Client", lambda *a, **k: _Client())

    service = DiscoveryService()
    records, stats = service._discover_documents()

    assert records == []
    assert stats["api_attempted"] is True
    assert stats["api_status"] == "451"
    assert stats["fallback_attempted"] is True
    assert stats["fallback_reason"] is not None
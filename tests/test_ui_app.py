from app.ui.app import (
    _api_headers,
    build_preview_payload,
    describe_evidence_result,
    extract_matrix_pair_from_diff_row,
    fetch_artifact_bytes,
    extract_source_document_version_ids,
    build_bulk_approve_evidence_ids,
    build_matrix_cell_detail_params,
    build_matrix_query_params,
    format_output_option_label,
    filter_document_artifacts,
    filter_document_items,
    filter_document_sections,
    filter_pipeline_runs,
    filter_recent_tasks,
    resolve_artifact_id,
    resolve_document_id,
    resolve_entity_id,
    resolve_history_target_id,
    resolve_output_id,
    resolve_review_target_id,
    resolve_task_id,
    search_recent_tasks,
    sort_document_items,
    sort_recent_tasks,
    translate_value_or_fallback,
    resolve_current_document_version_id,
    resolve_loaded_document_id,
)
from app.ui.ui_i18n import set_current_language


def test_build_matrix_query_params_omits_empty_optional_filters() -> None:
    params = build_matrix_query_params(
        page_size=50,
        scope_type="global",
        scope_id="   ",
        model_version_id=0,
        molecule_from_id=0,
    )

    assert params == {"page": 1, "page_size": 50, "scope_type": "global"}


def test_build_matrix_query_params_includes_all_present_filters() -> None:
    params = build_matrix_query_params(
        page_size=100,
        scope_type="disease",
        scope_id="ra",
        model_version_id=7,
        molecule_from_id=11,
    )

    assert params == {
        "page": 1,
        "page_size": 100,
        "scope_type": "disease",
        "scope_id": "ra",
        "model_version_id": 7,
        "molecule_from_id": 11,
    }


def test_build_matrix_cell_detail_params_omits_model_when_zero() -> None:
    params = build_matrix_cell_detail_params(
        molecule_from_id=1,
        molecule_to_id=2,
        scope_type="global",
        model_version_id=0,
    )

    assert params == {
        "molecule_from_id": 1,
        "molecule_to_id": 2,
        "scope_type": "global",
    }


def test_build_matrix_cell_detail_params_includes_model_when_present() -> None:
    params = build_matrix_cell_detail_params(
        molecule_from_id=1,
        molecule_to_id=2,
        scope_type="disease",
        model_version_id=9,
    )

    assert params == {
        "molecule_from_id": 1,
        "molecule_to_id": 2,
        "scope_type": "disease",
        "model_version_id": 9,
    }


def test_build_bulk_approve_evidence_ids_merges_manual_and_selected_without_dupes() -> None:
    evidence_ids = build_bulk_approve_evidence_ids("7, 8, 7", [8, 9, 10])

    assert evidence_ids == [7, 8, 9, 10]


def test_build_bulk_approve_evidence_ids_skips_empty_values() -> None:
    evidence_ids = build_bulk_approve_evidence_ids("  ,  ", [])

    assert evidence_ids == []


def test_resolve_review_target_id_prefers_queue_selection() -> None:
    assert resolve_review_target_id(5, 11) == 11


def test_resolve_review_target_id_falls_back_to_manual_value() -> None:
    assert resolve_review_target_id(5, None) == 5


def test_resolve_history_target_id_prefers_queue_selection() -> None:
    assert resolve_history_target_id(3, 12) == 12


def test_resolve_history_target_id_falls_back_to_manual_value() -> None:
    assert resolve_history_target_id(3, None) == 3


def test_resolve_document_id_prefers_current_list_selection() -> None:
    assert resolve_document_id(4, 15) == 15


def test_resolve_document_id_falls_back_to_manual_value() -> None:
    assert resolve_document_id(4, None) == 4


def test_resolve_loaded_document_id_updates_only_on_explicit_load() -> None:
    assert resolve_loaded_document_id(11, 4, None, False) == 11
    assert resolve_loaded_document_id(11, 4, 7, True) == 7
    assert resolve_loaded_document_id(None, 4, None, True) == 4


def test_resolve_output_id_prefers_current_list_selection() -> None:
    assert resolve_output_id(6, 18) == 18


def test_resolve_output_id_falls_back_to_manual_value() -> None:
    assert resolve_output_id(6, None) == 6


def test_resolve_artifact_id_prefers_current_list_selection() -> None:
    assert resolve_artifact_id(2, 21) == 21


def test_resolve_artifact_id_falls_back_to_manual_value() -> None:
    assert resolve_artifact_id(2, None) == 2


def test_resolve_entity_id_prefers_current_list_selection() -> None:
    assert resolve_entity_id(3, 31) == 31


def test_resolve_entity_id_falls_back_to_manual_value() -> None:
    assert resolve_entity_id(3, None) == 3


def test_resolve_task_id_prefers_current_selection() -> None:
    assert resolve_task_id("manual-task", "queued-task") == "queued-task"


def test_resolve_task_id_strips_manual_value() -> None:
    assert resolve_task_id("  manual-task  ", None) == "manual-task"


def test_filter_recent_tasks_returns_all_when_origin_empty() -> None:
    recent_tasks = [{"task_id": "1", "origin": "pipeline"}, {"task_id": "2", "origin": "review"}]

    assert filter_recent_tasks(recent_tasks, "") == recent_tasks


def test_filter_recent_tasks_keeps_only_matching_origin() -> None:
    recent_tasks = [{"task_id": "1", "origin": "pipeline"}, {"task_id": "2", "origin": "review"}]

    assert filter_recent_tasks(recent_tasks, "pipeline") == [{"task_id": "1", "origin": "pipeline"}]


def test_search_recent_tasks_returns_all_when_query_empty() -> None:
    recent_tasks = [{"task_id": "1", "label": "Sync Task"}, {"task_id": "2", "label": "Review Task"}]

    assert search_recent_tasks(recent_tasks, "  ") == recent_tasks


def test_search_recent_tasks_filters_case_insensitively() -> None:
    recent_tasks = [{"task_id": "1", "label": "Sync Task"}, {"task_id": "2", "label": "Review Task"}]

    assert search_recent_tasks(recent_tasks, "sync") == [{"task_id": "1", "label": "Sync Task"}]


def test_sort_recent_tasks_defaults_to_newest_first() -> None:
    recent_tasks = [
        {"task_id": "1", "queued_at": "2026-04-24T10:00:00+00:00"},
        {"task_id": "2", "queued_at": "2026-04-24T10:05:00+00:00"},
    ]

    assert [item["task_id"] for item in sort_recent_tasks(recent_tasks, "newest")] == ["2", "1"]


def test_sort_recent_tasks_supports_oldest_first() -> None:
    recent_tasks = [
        {"task_id": "1", "queued_at": "2026-04-24T10:00:00+00:00"},
        {"task_id": "2", "queued_at": "2026-04-24T10:05:00+00:00"},
    ]

    assert [item["task_id"] for item in sort_recent_tasks(recent_tasks, "oldest")] == ["1", "2"]


def test_filter_document_items_returns_all_when_status_empty() -> None:
    document_items = [{"id": 1, "status": "ready"}, {"id": 2, "status": "draft"}]

    assert filter_document_items(document_items, "") == document_items


def test_filter_document_items_keeps_only_matching_status() -> None:
    document_items = [{"id": 1, "status": "ready"}, {"id": 2, "status": "draft"}]

    assert filter_document_items(document_items, "ready") == [{"id": 1, "status": "ready"}]


def test_sort_document_items_defaults_to_newest_first() -> None:
    document_items = [{"id": 1}, {"id": 3}, {"id": 2}]

    assert [item["id"] for item in sort_document_items(document_items, "newest")] == [3, 2, 1]


def test_sort_document_items_supports_oldest_first() -> None:
    document_items = [{"id": 1}, {"id": 3}, {"id": 2}]

    assert [item["id"] for item in sort_document_items(document_items, "oldest")] == [1, 2, 3]


def test_filter_document_artifacts_returns_all_when_filter_empty() -> None:
    artifacts = [{"id": 1, "artifact_type": "pdf"}, {"id": 2, "artifact_type": "html"}]

    assert filter_document_artifacts(artifacts, "") == artifacts


def test_filter_document_artifacts_keeps_only_matching_type() -> None:
    artifacts = [{"id": 1, "artifact_type": "pdf"}, {"id": 2, "artifact_type": "html"}]

    assert filter_document_artifacts(artifacts, "pdf") == [{"id": 1, "artifact_type": "pdf"}]


def test_filter_document_sections_returns_all_when_query_empty() -> None:
    sections = [{"section_title": "Intro", "fragments": [{"fragment_text": "Alpha"}]}]

    assert filter_document_sections(sections, "") == sections


def test_filter_document_sections_matches_title_or_fragment_text() -> None:
    sections = [
        {"section_title": "Intro", "fragments": [{"fragment_text": "Alpha"}]},
        {"section_title": "Treatment", "fragments": [{"fragment_text": "Beta insulin"}]},
    ]

    assert filter_document_sections(sections, "insulin") == [
        {"section_title": "Treatment", "fragments": [{"fragment_text": "Beta insulin"}]}
    ]


def test_filter_pipeline_runs_returns_all_when_status_empty() -> None:
    run_items = [{"id": 1, "status": "completed"}, {"id": 2, "status": "failed"}]

    assert filter_pipeline_runs(run_items, "") == run_items


def test_filter_pipeline_runs_keeps_only_matching_status() -> None:
    run_items = [{"id": 1, "status": "completed"}, {"id": 2, "status": "failed"}]

    assert filter_pipeline_runs(run_items, "completed") == [{"id": 1, "status": "completed"}]


def test_translate_value_or_fallback_uses_localized_default_for_empty_value() -> None:
    set_current_language("en")
    assert translate_value_or_fallback(None) == "n/a"


def test_format_output_option_label_uses_fallback_title() -> None:
    set_current_language("en")
    formatted = format_output_option_label({"id": 7, "output_type": "memo", "title": None})

    assert formatted == "#7 | memo | Untitled"


def test_format_output_option_label_uses_unknown_type_fallback() -> None:
    set_current_language("en")
    formatted = format_output_option_label({"id": 8, "output_type": None, "title": "Demo"})

    assert formatted == "#8 | Unknown | Demo"


def test_resolve_current_document_version_id_prefers_is_current_flag() -> None:
    detail = {
        "versions": [
            {"id": 10, "is_current": False},
            {"id": 11, "is_current": True},
        ]
    }
    assert resolve_current_document_version_id(detail) == 11


def test_extract_source_document_version_ids_merges_links_and_manifest() -> None:
    artifact_detail = {
        "source_links": [
            {"source_kind": "document_version", "source_id": 5},
            {"source_kind": "artifact", "source_id": 99},
        ],
        "manifest_json": {"source_document_version_ids": [7, 5]},
    }
    assert extract_source_document_version_ids(artifact_detail) == [5, 7]


def test_extract_matrix_pair_from_diff_row_returns_none_for_invalid_payload() -> None:
    assert extract_matrix_pair_from_diff_row({"from": 1, "to": "bad"}) is None
    assert extract_matrix_pair_from_diff_row({"from": 2, "to": 3}) == (2, 3)


def test_api_headers_uses_configured_api_key(monkeypatch) -> None:
    monkeypatch.setenv("CRIN_API_KEY", "pilot-secret")
    assert _api_headers() == {"X-CRIN-API-Key": "pilot-secret"}


def test_fetch_artifact_bytes_uses_server_side_request_with_api_key(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Response:
        status_code = 200
        content = b"<html>artifact</html>"
        headers = {"content-type": "text/html"}

        def raise_for_status(self):
            return None

    def fake_get(url, *, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setenv("CRIN_API_KEY", "pilot-secret")
    monkeypatch.setattr("app.ui.app.httpx.get", fake_get)

    result = fetch_artifact_bytes(
        {
            "id": 40,
            "artifact_type": "html",
            "download_url": "/documents/1/artifacts/40/download",
        }
    )

    assert result["ok"] is True
    assert captured["url"] == "http://app:8000/documents/1/artifacts/40/download"
    assert captured["headers"] == {"X-CRIN-API-Key": "pilot-secret"}


def test_build_preview_payload_returns_text_for_html() -> None:
    payload = build_preview_payload(
        {
            "ok": True,
            "content_type": "text/html",
            "content": b"<html><body>clinical recommendation</body></html>",
        }
    )

    assert payload["kind"] == "text"
    assert "clinical recommendation" in payload["message"]


def test_build_preview_payload_returns_pdf_fallback_message() -> None:
    payload = build_preview_payload(
        {
            "ok": True,
            "content_type": "application/pdf",
            "content": b"%PDF-1.7",
        }
    )

    assert payload["kind"] == "info"
    assert "use Download" in payload["message"]


def test_describe_evidence_result_handles_rows_empty_and_error() -> None:
    rows_result = describe_evidence_result(
        {"ok": True, "data": {"items": [{"id": 1}], "total": 1}}
    )
    empty_result = describe_evidence_result(
        {"ok": True, "data": {"items": [], "total": 0}}
    )
    error_result = describe_evidence_result(
        {"ok": False, "status_code": 500, "detail": "server exploded"}
    )

    assert rows_result["state"] == "rows"
    assert rows_result["total"] == 1
    assert empty_result["state"] == "empty"
    assert empty_result["message"] == "No evidence rows for current version"
    assert error_result["state"] == "error"
    assert "500" in error_result["message"]
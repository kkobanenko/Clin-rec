from app.ui.app import (
    build_bulk_approve_evidence_ids,
    build_matrix_cell_detail_params,
    build_matrix_query_params,
    filter_document_artifacts,
    filter_document_items,
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
)


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
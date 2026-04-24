from app.ui.app import (
    build_bulk_approve_evidence_ids,
    build_matrix_cell_detail_params,
    build_matrix_query_params,
    resolve_document_id,
    resolve_history_target_id,
    resolve_output_id,
    resolve_review_target_id,
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
from app.ui.app import (
    build_bulk_approve_evidence_ids,
    build_matrix_cell_detail_params,
    build_matrix_query_params,
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
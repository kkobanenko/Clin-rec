from app.ui.app import build_matrix_query_params


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
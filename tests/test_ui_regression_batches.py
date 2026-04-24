
"""Large regression batches for UI helper pure functions."""

from app.ui.app import (
    _split_frontmatter,
    append_recent_task,
    build_bulk_approve_evidence_ids,
    build_matrix_cell_detail_params,
    build_matrix_query_params,
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
)



class TestUiRegressionBatch01:
    def test_append_recent_task_prepends_and_dedupes_01(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_01(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew01", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_01(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_01(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_01(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_01(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_01(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_01(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_01(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_01(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_01(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_01(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_01(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_01(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_01(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_01(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch02:
    def test_append_recent_task_prepends_and_dedupes_02(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_02(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew02", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_02(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_02(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_02(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_02(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_02(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_02(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_02(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_02(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_02(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_02(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_02(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_02(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_02(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_02(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch03:
    def test_append_recent_task_prepends_and_dedupes_03(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_03(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew03", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_03(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_03(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_03(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_03(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_03(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_03(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_03(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_03(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_03(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_03(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_03(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_03(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_03(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_03(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch04:
    def test_append_recent_task_prepends_and_dedupes_04(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_04(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew04", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_04(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_04(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_04(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_04(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_04(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_04(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_04(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_04(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_04(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_04(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_04(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_04(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_04(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_04(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch05:
    def test_append_recent_task_prepends_and_dedupes_05(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_05(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew05", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_05(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_05(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_05(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_05(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_05(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_05(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_05(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_05(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_05(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_05(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_05(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_05(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_05(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_05(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch06:
    def test_append_recent_task_prepends_and_dedupes_06(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_06(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew06", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_06(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_06(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_06(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_06(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_06(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_06(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_06(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_06(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_06(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_06(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_06(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_06(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_06(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_06(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch07:
    def test_append_recent_task_prepends_and_dedupes_07(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_07(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew07", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_07(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_07(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_07(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_07(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_07(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_07(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_07(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_07(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_07(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_07(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_07(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_07(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_07(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_07(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch08:
    def test_append_recent_task_prepends_and_dedupes_08(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_08(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew08", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_08(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_08(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_08(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_08(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_08(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_08(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_08(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_08(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_08(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_08(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_08(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_08(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_08(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_08(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch09:
    def test_append_recent_task_prepends_and_dedupes_09(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_09(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew09", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_09(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_09(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_09(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_09(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_09(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_09(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_09(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_09(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_09(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_09(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_09(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_09(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_09(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_09(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch10:
    def test_append_recent_task_prepends_and_dedupes_10(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_10(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew10", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_10(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_10(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_10(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_10(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_10(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_10(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_10(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_10(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_10(self):
        docs = [
            {"id": 2, "status": "active"},
            {"id": 1, "status": "draft"},
            {"id": 3, "status": "active"},
        ]
        filtered = filter_document_items(docs, "active")
        newest = sort_document_items(filtered, "newest")
        oldest = sort_document_items(filtered, "oldest")
        assert [d["id"] for d in newest] == [3, 2]
        assert [d["id"] for d in oldest] == [2, 3]

    def test_filter_document_artifacts_10(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_10(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_10(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_10(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_10(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text

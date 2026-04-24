
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


class TestUiRegressionBatch11:
    def test_append_recent_task_prepends_and_dedupes_11(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_11(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew11", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_11(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_11(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_11(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_11(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_11(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_11(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_11(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_11(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_11(self):
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

    def test_filter_document_artifacts_11(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_11(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_11(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_11(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_11(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch12:
    def test_append_recent_task_prepends_and_dedupes_12(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_12(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew12", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_12(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_12(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_12(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_12(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_12(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_12(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_12(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_12(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_12(self):
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

    def test_filter_document_artifacts_12(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_12(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_12(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_12(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_12(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch13:
    def test_append_recent_task_prepends_and_dedupes_13(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_13(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew13", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_13(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_13(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_13(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_13(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_13(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_13(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_13(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_13(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_13(self):
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

    def test_filter_document_artifacts_13(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_13(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_13(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_13(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_13(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch14:
    def test_append_recent_task_prepends_and_dedupes_14(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_14(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew14", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_14(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_14(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_14(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_14(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_14(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_14(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_14(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_14(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_14(self):
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

    def test_filter_document_artifacts_14(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_14(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_14(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_14(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_14(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch15:
    def test_append_recent_task_prepends_and_dedupes_15(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_15(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew15", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_15(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_15(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_15(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_15(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_15(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_15(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_15(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_15(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_15(self):
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

    def test_filter_document_artifacts_15(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_15(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_15(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_15(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_15(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch16:
    def test_append_recent_task_prepends_and_dedupes_16(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_16(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew16", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_16(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_16(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_16(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_16(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_16(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_16(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_16(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_16(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_16(self):
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

    def test_filter_document_artifacts_16(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_16(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_16(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_16(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_16(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch17:
    def test_append_recent_task_prepends_and_dedupes_17(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_17(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew17", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_17(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_17(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_17(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_17(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_17(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_17(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_17(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_17(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_17(self):
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

    def test_filter_document_artifacts_17(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_17(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_17(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_17(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_17(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch18:
    def test_append_recent_task_prepends_and_dedupes_18(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_18(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew18", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_18(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_18(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_18(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_18(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_18(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_18(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_18(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_18(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_18(self):
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

    def test_filter_document_artifacts_18(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_18(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_18(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_18(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_18(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch19:
    def test_append_recent_task_prepends_and_dedupes_19(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_19(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew19", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_19(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_19(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_19(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_19(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_19(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_19(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_19(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_19(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_19(self):
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

    def test_filter_document_artifacts_19(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_19(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_19(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_19(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_19(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch20:
    def test_append_recent_task_prepends_and_dedupes_20(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_20(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew20", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_20(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_20(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_20(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_20(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_20(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_20(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_20(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_20(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_20(self):
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

    def test_filter_document_artifacts_20(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_20(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_20(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_20(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_20(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch21:
    def test_append_recent_task_prepends_and_dedupes_21(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_21(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew21", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_21(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_21(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_21(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_21(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_21(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_21(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_21(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_21(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_21(self):
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

    def test_filter_document_artifacts_21(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_21(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_21(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_21(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_21(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch22:
    def test_append_recent_task_prepends_and_dedupes_22(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_22(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew22", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_22(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_22(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_22(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_22(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_22(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_22(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_22(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_22(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_22(self):
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

    def test_filter_document_artifacts_22(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_22(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_22(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_22(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_22(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch23:
    def test_append_recent_task_prepends_and_dedupes_23(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_23(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew23", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_23(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_23(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_23(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_23(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_23(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_23(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_23(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_23(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_23(self):
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

    def test_filter_document_artifacts_23(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_23(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_23(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_23(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_23(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch24:
    def test_append_recent_task_prepends_and_dedupes_24(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_24(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew24", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_24(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_24(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_24(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_24(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_24(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_24(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_24(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_24(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_24(self):
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

    def test_filter_document_artifacts_24(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_24(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_24(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_24(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_24(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch25:
    def test_append_recent_task_prepends_and_dedupes_25(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_25(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew25", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_25(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_25(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_25(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_25(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_25(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_25(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_25(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_25(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_25(self):
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

    def test_filter_document_artifacts_25(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_25(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_25(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_25(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_25(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch26:
    def test_append_recent_task_prepends_and_dedupes_26(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_26(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew26", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_26(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_26(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_26(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_26(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_26(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_26(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_26(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_26(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_26(self):
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

    def test_filter_document_artifacts_26(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_26(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_26(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_26(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_26(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch27:
    def test_append_recent_task_prepends_and_dedupes_27(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_27(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew27", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_27(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_27(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_27(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_27(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_27(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_27(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_27(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_27(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_27(self):
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

    def test_filter_document_artifacts_27(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_27(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_27(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_27(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_27(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch28:
    def test_append_recent_task_prepends_and_dedupes_28(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_28(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew28", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_28(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_28(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_28(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_28(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_28(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_28(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_28(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_28(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_28(self):
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

    def test_filter_document_artifacts_28(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_28(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_28(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_28(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_28(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch29:
    def test_append_recent_task_prepends_and_dedupes_29(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_29(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew29", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_29(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_29(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_29(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_29(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_29(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_29(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_29(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_29(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_29(self):
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

    def test_filter_document_artifacts_29(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_29(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_29(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_29(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_29(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch30:
    def test_append_recent_task_prepends_and_dedupes_30(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_30(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew30", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_30(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_30(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_30(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_30(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_30(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_30(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_30(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_30(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_30(self):
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

    def test_filter_document_artifacts_30(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_30(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_30(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_30(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_30(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch31:
    def test_append_recent_task_prepends_and_dedupes_31(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_31(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew31", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_31(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_31(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_31(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_31(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_31(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_31(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_31(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_31(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_31(self):
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

    def test_filter_document_artifacts_31(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_31(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_31(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_31(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_31(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch32:
    def test_append_recent_task_prepends_and_dedupes_32(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_32(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew32", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_32(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_32(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_32(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_32(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_32(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_32(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_32(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_32(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_32(self):
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

    def test_filter_document_artifacts_32(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_32(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_32(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_32(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_32(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch33:
    def test_append_recent_task_prepends_and_dedupes_33(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_33(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew33", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_33(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_33(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_33(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_33(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_33(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_33(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_33(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_33(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_33(self):
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

    def test_filter_document_artifacts_33(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_33(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_33(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_33(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_33(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch34:
    def test_append_recent_task_prepends_and_dedupes_34(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_34(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew34", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_34(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_34(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_34(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_34(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_34(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_34(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_34(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_34(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_34(self):
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

    def test_filter_document_artifacts_34(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_34(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_34(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_34(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_34(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch35:
    def test_append_recent_task_prepends_and_dedupes_35(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_35(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew35", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_35(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_35(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_35(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_35(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_35(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_35(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_35(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_35(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_35(self):
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

    def test_filter_document_artifacts_35(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_35(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_35(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_35(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_35(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch36:
    def test_append_recent_task_prepends_and_dedupes_36(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_36(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew36", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_36(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_36(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_36(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_36(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_36(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_36(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_36(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_36(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_36(self):
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

    def test_filter_document_artifacts_36(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_36(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_36(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_36(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_36(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch37:
    def test_append_recent_task_prepends_and_dedupes_37(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_37(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew37", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_37(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_37(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_37(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_37(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_37(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_37(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_37(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_37(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_37(self):
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

    def test_filter_document_artifacts_37(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_37(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_37(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_37(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_37(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch38:
    def test_append_recent_task_prepends_and_dedupes_38(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_38(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew38", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_38(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_38(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_38(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_38(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_38(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_38(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_38(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_38(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_38(self):
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

    def test_filter_document_artifacts_38(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_38(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_38(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_38(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_38(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch39:
    def test_append_recent_task_prepends_and_dedupes_39(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_39(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew39", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_39(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_39(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_39(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_39(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_39(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_39(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_39(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_39(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_39(self):
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

    def test_filter_document_artifacts_39(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_39(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_39(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_39(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_39(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch40:
    def test_append_recent_task_prepends_and_dedupes_40(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_40(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew40", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_40(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_40(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_40(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_40(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_40(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_40(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_40(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_40(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_40(self):
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

    def test_filter_document_artifacts_40(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_40(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_40(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_40(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_40(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch41:
    def test_append_recent_task_prepends_and_dedupes_41(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_41(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew41", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_41(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_41(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_41(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_41(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_41(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_41(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_41(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_41(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_41(self):
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

    def test_filter_document_artifacts_41(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_41(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_41(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_41(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_41(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch42:
    def test_append_recent_task_prepends_and_dedupes_42(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_42(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew42", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_42(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_42(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_42(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_42(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_42(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_42(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_42(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_42(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_42(self):
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

    def test_filter_document_artifacts_42(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_42(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_42(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_42(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_42(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch43:
    def test_append_recent_task_prepends_and_dedupes_43(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_43(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew43", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_43(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_43(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_43(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_43(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_43(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_43(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_43(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_43(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_43(self):
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

    def test_filter_document_artifacts_43(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_43(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_43(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_43(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_43(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch44:
    def test_append_recent_task_prepends_and_dedupes_44(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_44(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew44", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_44(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_44(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_44(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_44(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_44(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_44(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_44(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_44(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_44(self):
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

    def test_filter_document_artifacts_44(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_44(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_44(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_44(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_44(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch45:
    def test_append_recent_task_prepends_and_dedupes_45(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_45(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew45", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_45(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_45(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_45(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_45(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_45(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_45(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_45(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_45(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_45(self):
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

    def test_filter_document_artifacts_45(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_45(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_45(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_45(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_45(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch46:
    def test_append_recent_task_prepends_and_dedupes_46(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_46(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew46", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_46(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_46(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_46(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_46(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_46(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_46(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_46(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_46(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_46(self):
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

    def test_filter_document_artifacts_46(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_46(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_46(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_46(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_46(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch47:
    def test_append_recent_task_prepends_and_dedupes_47(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_47(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew47", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_47(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_47(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_47(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_47(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_47(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_47(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_47(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_47(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_47(self):
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

    def test_filter_document_artifacts_47(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_47(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_47(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_47(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_47(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch48:
    def test_append_recent_task_prepends_and_dedupes_48(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_48(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew48", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_48(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_48(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_48(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_48(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_48(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_48(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_48(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_48(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_48(self):
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

    def test_filter_document_artifacts_48(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_48(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_48(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_48(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_48(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch49:
    def test_append_recent_task_prepends_and_dedupes_49(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_49(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew49", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_49(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_49(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_49(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_49(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_49(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_49(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_49(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_49(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_49(self):
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

    def test_filter_document_artifacts_49(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_49(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_49(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_49(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_49(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch50:
    def test_append_recent_task_prepends_and_dedupes_50(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_50(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew50", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_50(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_50(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_50(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_50(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_50(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_50(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_50(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_50(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_50(self):
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

    def test_filter_document_artifacts_50(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_50(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_50(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_50(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_50(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch051:
    def test_append_recent_task_prepends_and_dedupes_051(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_051(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew051", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_051(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_051(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_051(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_051(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_051(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_051(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_051(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_051(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_051(self):
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

    def test_filter_document_artifacts_051(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_051(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_051(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_051(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_051(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch052:
    def test_append_recent_task_prepends_and_dedupes_052(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_052(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew052", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_052(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_052(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_052(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_052(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_052(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_052(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_052(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_052(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_052(self):
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

    def test_filter_document_artifacts_052(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_052(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_052(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_052(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_052(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch053:
    def test_append_recent_task_prepends_and_dedupes_053(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_053(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew053", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_053(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_053(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_053(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_053(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_053(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_053(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_053(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_053(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_053(self):
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

    def test_filter_document_artifacts_053(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_053(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_053(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_053(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_053(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch054:
    def test_append_recent_task_prepends_and_dedupes_054(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_054(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew054", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_054(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_054(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_054(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_054(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_054(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_054(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_054(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_054(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_054(self):
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

    def test_filter_document_artifacts_054(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_054(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_054(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_054(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_054(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch055:
    def test_append_recent_task_prepends_and_dedupes_055(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_055(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew055", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_055(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_055(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_055(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_055(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_055(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_055(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_055(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_055(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_055(self):
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

    def test_filter_document_artifacts_055(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_055(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_055(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_055(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_055(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch056:
    def test_append_recent_task_prepends_and_dedupes_056(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_056(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew056", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_056(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_056(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_056(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_056(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_056(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_056(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_056(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_056(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_056(self):
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

    def test_filter_document_artifacts_056(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_056(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_056(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_056(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_056(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch057:
    def test_append_recent_task_prepends_and_dedupes_057(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_057(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew057", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_057(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_057(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_057(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_057(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_057(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_057(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_057(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_057(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_057(self):
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

    def test_filter_document_artifacts_057(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_057(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_057(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_057(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_057(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch058:
    def test_append_recent_task_prepends_and_dedupes_058(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_058(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew058", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_058(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_058(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_058(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_058(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_058(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_058(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_058(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_058(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_058(self):
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

    def test_filter_document_artifacts_058(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_058(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_058(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_058(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_058(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch059:
    def test_append_recent_task_prepends_and_dedupes_059(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_059(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew059", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_059(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_059(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_059(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_059(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_059(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_059(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_059(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_059(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_059(self):
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

    def test_filter_document_artifacts_059(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_059(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_059(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_059(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_059(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch060:
    def test_append_recent_task_prepends_and_dedupes_060(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_060(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew060", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_060(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_060(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_060(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_060(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_060(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_060(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_060(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_060(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_060(self):
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

    def test_filter_document_artifacts_060(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_060(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_060(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_060(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_060(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch061:
    def test_append_recent_task_prepends_and_dedupes_061(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_061(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew061", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_061(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_061(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_061(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_061(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_061(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_061(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_061(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_061(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_061(self):
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

    def test_filter_document_artifacts_061(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_061(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_061(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_061(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_061(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch062:
    def test_append_recent_task_prepends_and_dedupes_062(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_062(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew062", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_062(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_062(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_062(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_062(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_062(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_062(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_062(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_062(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_062(self):
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

    def test_filter_document_artifacts_062(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_062(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_062(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_062(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_062(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch063:
    def test_append_recent_task_prepends_and_dedupes_063(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_063(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew063", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_063(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_063(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_063(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_063(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_063(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_063(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_063(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_063(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_063(self):
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

    def test_filter_document_artifacts_063(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_063(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_063(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_063(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_063(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch064:
    def test_append_recent_task_prepends_and_dedupes_064(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_064(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew064", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_064(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_064(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_064(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_064(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_064(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_064(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_064(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_064(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_064(self):
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

    def test_filter_document_artifacts_064(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_064(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_064(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_064(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_064(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch065:
    def test_append_recent_task_prepends_and_dedupes_065(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_065(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew065", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_065(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_065(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_065(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_065(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_065(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_065(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_065(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_065(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_065(self):
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

    def test_filter_document_artifacts_065(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_065(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_065(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_065(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_065(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch066:
    def test_append_recent_task_prepends_and_dedupes_066(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_066(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew066", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_066(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_066(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_066(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_066(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_066(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_066(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_066(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_066(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_066(self):
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

    def test_filter_document_artifacts_066(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_066(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_066(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_066(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_066(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch067:
    def test_append_recent_task_prepends_and_dedupes_067(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_067(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew067", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_067(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_067(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_067(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_067(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_067(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_067(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_067(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_067(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_067(self):
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

    def test_filter_document_artifacts_067(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_067(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_067(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_067(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_067(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch068:
    def test_append_recent_task_prepends_and_dedupes_068(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_068(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew068", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_068(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_068(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_068(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_068(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_068(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_068(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_068(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_068(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_068(self):
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

    def test_filter_document_artifacts_068(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_068(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_068(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_068(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_068(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch069:
    def test_append_recent_task_prepends_and_dedupes_069(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_069(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew069", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_069(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_069(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_069(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_069(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_069(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_069(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_069(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_069(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_069(self):
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

    def test_filter_document_artifacts_069(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_069(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_069(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_069(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_069(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch070:
    def test_append_recent_task_prepends_and_dedupes_070(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_070(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew070", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_070(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_070(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_070(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_070(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_070(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_070(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_070(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_070(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_070(self):
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

    def test_filter_document_artifacts_070(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_070(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_070(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_070(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_070(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch071:
    def test_append_recent_task_prepends_and_dedupes_071(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_071(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew071", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_071(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_071(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_071(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_071(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_071(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_071(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_071(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_071(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_071(self):
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

    def test_filter_document_artifacts_071(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_071(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_071(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_071(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_071(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch072:
    def test_append_recent_task_prepends_and_dedupes_072(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_072(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew072", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_072(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_072(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_072(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_072(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_072(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_072(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_072(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_072(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_072(self):
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

    def test_filter_document_artifacts_072(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_072(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_072(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_072(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_072(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch073:
    def test_append_recent_task_prepends_and_dedupes_073(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_073(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew073", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_073(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_073(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_073(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_073(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_073(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_073(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_073(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_073(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_073(self):
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

    def test_filter_document_artifacts_073(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_073(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_073(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_073(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_073(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch074:
    def test_append_recent_task_prepends_and_dedupes_074(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_074(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew074", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_074(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_074(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_074(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_074(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_074(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_074(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_074(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_074(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_074(self):
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

    def test_filter_document_artifacts_074(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_074(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_074(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_074(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_074(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch075:
    def test_append_recent_task_prepends_and_dedupes_075(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_075(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew075", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_075(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_075(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_075(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_075(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_075(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_075(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_075(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_075(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_075(self):
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

    def test_filter_document_artifacts_075(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_075(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_075(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_075(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_075(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch076:
    def test_append_recent_task_prepends_and_dedupes_076(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_076(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew076", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_076(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_076(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_076(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_076(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_076(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_076(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_076(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_076(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_076(self):
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

    def test_filter_document_artifacts_076(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_076(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_076(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_076(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_076(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch077:
    def test_append_recent_task_prepends_and_dedupes_077(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_077(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew077", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_077(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_077(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_077(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_077(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_077(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_077(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_077(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_077(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_077(self):
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

    def test_filter_document_artifacts_077(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_077(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_077(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_077(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_077(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch078:
    def test_append_recent_task_prepends_and_dedupes_078(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_078(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew078", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_078(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_078(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_078(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_078(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_078(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_078(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_078(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_078(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_078(self):
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

    def test_filter_document_artifacts_078(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_078(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_078(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_078(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_078(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch079:
    def test_append_recent_task_prepends_and_dedupes_079(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_079(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew079", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_079(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_079(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_079(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_079(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_079(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_079(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_079(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_079(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_079(self):
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

    def test_filter_document_artifacts_079(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_079(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_079(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_079(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_079(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch080:
    def test_append_recent_task_prepends_and_dedupes_080(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_080(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew080", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_080(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_080(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_080(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_080(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_080(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_080(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_080(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_080(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_080(self):
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

    def test_filter_document_artifacts_080(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_080(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_080(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_080(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_080(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch081:
    def test_append_recent_task_prepends_and_dedupes_081(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_081(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew081", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_081(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_081(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_081(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_081(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_081(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_081(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_081(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_081(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_081(self):
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

    def test_filter_document_artifacts_081(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_081(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_081(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_081(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_081(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch082:
    def test_append_recent_task_prepends_and_dedupes_082(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_082(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew082", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_082(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_082(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_082(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_082(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_082(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_082(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_082(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_082(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_082(self):
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

    def test_filter_document_artifacts_082(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_082(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_082(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_082(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_082(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch083:
    def test_append_recent_task_prepends_and_dedupes_083(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_083(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew083", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_083(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_083(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_083(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_083(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_083(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_083(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_083(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_083(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_083(self):
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

    def test_filter_document_artifacts_083(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_083(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_083(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_083(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_083(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch084:
    def test_append_recent_task_prepends_and_dedupes_084(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_084(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew084", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_084(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_084(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_084(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_084(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_084(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_084(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_084(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_084(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_084(self):
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

    def test_filter_document_artifacts_084(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_084(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_084(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_084(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_084(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch085:
    def test_append_recent_task_prepends_and_dedupes_085(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_085(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew085", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_085(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_085(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_085(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_085(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_085(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_085(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_085(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_085(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_085(self):
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

    def test_filter_document_artifacts_085(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_085(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_085(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_085(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_085(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch086:
    def test_append_recent_task_prepends_and_dedupes_086(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_086(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew086", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_086(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_086(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_086(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_086(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_086(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_086(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_086(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_086(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_086(self):
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

    def test_filter_document_artifacts_086(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_086(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_086(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_086(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_086(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch087:
    def test_append_recent_task_prepends_and_dedupes_087(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_087(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew087", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_087(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_087(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_087(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_087(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_087(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_087(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_087(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_087(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_087(self):
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

    def test_filter_document_artifacts_087(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_087(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_087(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_087(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_087(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch088:
    def test_append_recent_task_prepends_and_dedupes_088(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_088(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew088", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_088(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_088(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_088(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_088(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_088(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_088(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_088(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_088(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_088(self):
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

    def test_filter_document_artifacts_088(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_088(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_088(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_088(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_088(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch089:
    def test_append_recent_task_prepends_and_dedupes_089(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_089(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew089", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_089(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_089(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_089(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_089(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_089(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_089(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_089(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_089(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_089(self):
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

    def test_filter_document_artifacts_089(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_089(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_089(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_089(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_089(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch090:
    def test_append_recent_task_prepends_and_dedupes_090(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_090(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew090", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_090(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_090(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_090(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_090(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_090(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_090(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_090(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_090(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_090(self):
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

    def test_filter_document_artifacts_090(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_090(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_090(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_090(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_090(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch091:
    def test_append_recent_task_prepends_and_dedupes_091(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_091(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew091", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_091(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_091(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_091(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_091(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_091(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_091(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_091(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_091(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_091(self):
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

    def test_filter_document_artifacts_091(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_091(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_091(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_091(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_091(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch092:
    def test_append_recent_task_prepends_and_dedupes_092(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_092(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew092", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_092(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_092(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_092(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_092(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_092(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_092(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_092(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_092(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_092(self):
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

    def test_filter_document_artifacts_092(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_092(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_092(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_092(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_092(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch093:
    def test_append_recent_task_prepends_and_dedupes_093(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_093(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew093", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_093(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_093(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_093(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_093(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_093(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_093(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_093(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_093(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_093(self):
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

    def test_filter_document_artifacts_093(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_093(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_093(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_093(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_093(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch094:
    def test_append_recent_task_prepends_and_dedupes_094(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_094(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew094", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_094(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_094(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_094(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_094(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_094(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_094(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_094(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_094(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_094(self):
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

    def test_filter_document_artifacts_094(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_094(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_094(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_094(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_094(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch095:
    def test_append_recent_task_prepends_and_dedupes_095(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_095(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew095", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_095(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_095(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_095(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_095(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_095(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_095(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_095(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_095(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_095(self):
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

    def test_filter_document_artifacts_095(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_095(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_095(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_095(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_095(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch096:
    def test_append_recent_task_prepends_and_dedupes_096(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_096(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew096", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_096(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_096(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_096(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_096(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_096(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_096(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_096(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_096(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_096(self):
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

    def test_filter_document_artifacts_096(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_096(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_096(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_096(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_096(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch097:
    def test_append_recent_task_prepends_and_dedupes_097(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_097(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew097", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_097(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_097(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_097(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_097(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_097(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_097(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_097(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_097(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_097(self):
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

    def test_filter_document_artifacts_097(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_097(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_097(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_097(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_097(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch098:
    def test_append_recent_task_prepends_and_dedupes_098(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_098(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew098", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_098(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_098(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_098(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_098(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_098(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_098(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_098(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_098(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_098(self):
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

    def test_filter_document_artifacts_098(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_098(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_098(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_098(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_098(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch099:
    def test_append_recent_task_prepends_and_dedupes_099(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_099(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew099", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_099(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_099(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_099(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_099(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_099(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_099(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_099(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_099(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_099(self):
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

    def test_filter_document_artifacts_099(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_099(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_099(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_099(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_099(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch100:
    def test_append_recent_task_prepends_and_dedupes_100(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_100(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew100", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_100(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_100(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_100(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_100(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_100(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_100(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_100(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_100(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_100(self):
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

    def test_filter_document_artifacts_100(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_100(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_100(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_100(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_100(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch101:
    def test_append_recent_task_prepends_and_dedupes_101(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_101(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew101", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_101(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_101(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_101(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_101(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_101(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_101(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_101(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_101(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_101(self):
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

    def test_filter_document_artifacts_101(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_101(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_101(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_101(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_101(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch102:
    def test_append_recent_task_prepends_and_dedupes_102(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_102(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew102", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_102(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_102(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_102(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_102(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_102(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_102(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_102(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_102(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_102(self):
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

    def test_filter_document_artifacts_102(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_102(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_102(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_102(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_102(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch103:
    def test_append_recent_task_prepends_and_dedupes_103(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_103(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew103", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_103(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_103(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_103(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_103(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_103(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_103(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_103(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_103(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_103(self):
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

    def test_filter_document_artifacts_103(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_103(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_103(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_103(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_103(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch104:
    def test_append_recent_task_prepends_and_dedupes_104(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_104(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew104", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_104(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_104(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_104(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_104(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_104(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_104(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_104(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_104(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_104(self):
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

    def test_filter_document_artifacts_104(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_104(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_104(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_104(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_104(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch105:
    def test_append_recent_task_prepends_and_dedupes_105(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_105(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew105", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_105(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_105(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_105(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_105(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_105(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_105(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_105(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_105(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_105(self):
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

    def test_filter_document_artifacts_105(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_105(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_105(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_105(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_105(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch106:
    def test_append_recent_task_prepends_and_dedupes_106(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_106(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew106", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_106(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_106(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_106(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_106(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_106(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_106(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_106(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_106(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_106(self):
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

    def test_filter_document_artifacts_106(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_106(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_106(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_106(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_106(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch107:
    def test_append_recent_task_prepends_and_dedupes_107(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_107(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew107", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_107(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_107(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_107(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_107(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_107(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_107(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_107(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_107(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_107(self):
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

    def test_filter_document_artifacts_107(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_107(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_107(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_107(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_107(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch108:
    def test_append_recent_task_prepends_and_dedupes_108(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_108(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew108", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_108(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_108(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_108(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_108(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_108(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_108(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_108(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_108(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_108(self):
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

    def test_filter_document_artifacts_108(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_108(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_108(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_108(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_108(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch109:
    def test_append_recent_task_prepends_and_dedupes_109(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_109(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew109", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_109(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_109(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_109(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_109(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_109(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_109(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_109(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_109(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_109(self):
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

    def test_filter_document_artifacts_109(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_109(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_109(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_109(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_109(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch110:
    def test_append_recent_task_prepends_and_dedupes_110(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_110(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew110", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_110(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_110(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_110(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_110(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_110(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_110(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_110(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_110(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_110(self):
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

    def test_filter_document_artifacts_110(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_110(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_110(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_110(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_110(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch111:
    def test_append_recent_task_prepends_and_dedupes_111(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_111(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew111", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_111(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_111(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_111(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_111(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_111(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_111(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_111(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_111(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_111(self):
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

    def test_filter_document_artifacts_111(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_111(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_111(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_111(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_111(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch112:
    def test_append_recent_task_prepends_and_dedupes_112(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_112(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew112", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_112(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_112(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_112(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_112(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_112(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_112(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_112(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_112(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_112(self):
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

    def test_filter_document_artifacts_112(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_112(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_112(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_112(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_112(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch113:
    def test_append_recent_task_prepends_and_dedupes_113(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_113(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew113", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_113(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_113(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_113(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_113(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_113(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_113(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_113(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_113(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_113(self):
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

    def test_filter_document_artifacts_113(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_113(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_113(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_113(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_113(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch114:
    def test_append_recent_task_prepends_and_dedupes_114(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_114(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew114", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_114(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_114(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_114(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_114(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_114(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_114(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_114(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_114(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_114(self):
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

    def test_filter_document_artifacts_114(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_114(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_114(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_114(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_114(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch115:
    def test_append_recent_task_prepends_and_dedupes_115(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_115(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew115", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_115(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_115(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_115(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_115(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_115(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_115(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_115(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_115(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_115(self):
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

    def test_filter_document_artifacts_115(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_115(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_115(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_115(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_115(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch116:
    def test_append_recent_task_prepends_and_dedupes_116(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_116(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew116", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_116(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_116(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_116(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_116(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_116(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_116(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_116(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_116(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_116(self):
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

    def test_filter_document_artifacts_116(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_116(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_116(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_116(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_116(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch117:
    def test_append_recent_task_prepends_and_dedupes_117(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_117(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew117", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_117(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_117(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_117(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_117(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_117(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_117(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_117(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_117(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_117(self):
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

    def test_filter_document_artifacts_117(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_117(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_117(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_117(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_117(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch118:
    def test_append_recent_task_prepends_and_dedupes_118(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_118(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew118", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_118(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_118(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_118(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_118(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_118(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_118(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_118(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_118(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_118(self):
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

    def test_filter_document_artifacts_118(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_118(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_118(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_118(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_118(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch119:
    def test_append_recent_task_prepends_and_dedupes_119(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_119(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew119", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_119(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_119(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_119(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_119(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_119(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_119(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_119(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_119(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_119(self):
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

    def test_filter_document_artifacts_119(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_119(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_119(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_119(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_119(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch120:
    def test_append_recent_task_prepends_and_dedupes_120(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_120(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew120", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_120(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_120(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_120(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_120(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_120(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_120(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_120(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_120(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_120(self):
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

    def test_filter_document_artifacts_120(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_120(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_120(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_120(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_120(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch121:
    def test_append_recent_task_prepends_and_dedupes_121(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_121(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew121", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_121(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_121(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_121(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_121(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_121(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_121(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_121(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_121(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_121(self):
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

    def test_filter_document_artifacts_121(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_121(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_121(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_121(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_121(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch122:
    def test_append_recent_task_prepends_and_dedupes_122(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_122(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew122", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_122(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_122(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_122(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_122(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_122(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_122(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_122(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_122(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_122(self):
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

    def test_filter_document_artifacts_122(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_122(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_122(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_122(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_122(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch123:
    def test_append_recent_task_prepends_and_dedupes_123(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_123(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew123", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_123(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_123(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_123(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_123(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_123(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_123(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_123(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_123(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_123(self):
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

    def test_filter_document_artifacts_123(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_123(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_123(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_123(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_123(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch124:
    def test_append_recent_task_prepends_and_dedupes_124(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_124(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew124", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_124(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_124(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_124(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_124(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_124(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_124(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_124(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_124(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_124(self):
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

    def test_filter_document_artifacts_124(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_124(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_124(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_124(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_124(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch125:
    def test_append_recent_task_prepends_and_dedupes_125(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_125(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew125", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_125(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_125(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_125(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_125(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_125(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_125(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_125(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_125(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_125(self):
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

    def test_filter_document_artifacts_125(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_125(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_125(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_125(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_125(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch126:
    def test_append_recent_task_prepends_and_dedupes_126(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_126(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew126", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_126(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_126(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_126(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_126(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_126(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_126(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_126(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_126(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_126(self):
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

    def test_filter_document_artifacts_126(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_126(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_126(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_126(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_126(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch127:
    def test_append_recent_task_prepends_and_dedupes_127(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_127(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew127", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_127(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_127(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_127(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_127(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_127(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_127(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_127(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_127(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_127(self):
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

    def test_filter_document_artifacts_127(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_127(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_127(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_127(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_127(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch128:
    def test_append_recent_task_prepends_and_dedupes_128(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_128(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew128", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_128(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_128(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_128(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_128(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_128(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_128(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_128(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_128(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_128(self):
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

    def test_filter_document_artifacts_128(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_128(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_128(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_128(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_128(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch129:
    def test_append_recent_task_prepends_and_dedupes_129(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_129(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew129", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_129(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_129(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_129(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_129(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_129(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_129(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_129(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_129(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_129(self):
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

    def test_filter_document_artifacts_129(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_129(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_129(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_129(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_129(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch130:
    def test_append_recent_task_prepends_and_dedupes_130(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_130(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew130", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_130(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_130(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_130(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_130(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_130(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_130(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_130(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_130(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_130(self):
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

    def test_filter_document_artifacts_130(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_130(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_130(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_130(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_130(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch131:
    def test_append_recent_task_prepends_and_dedupes_131(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_131(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew131", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_131(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_131(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_131(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_131(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_131(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_131(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_131(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_131(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_131(self):
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

    def test_filter_document_artifacts_131(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_131(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_131(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_131(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_131(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch132:
    def test_append_recent_task_prepends_and_dedupes_132(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_132(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew132", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_132(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_132(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_132(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_132(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_132(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_132(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_132(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_132(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_132(self):
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

    def test_filter_document_artifacts_132(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_132(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_132(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_132(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_132(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch133:
    def test_append_recent_task_prepends_and_dedupes_133(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_133(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew133", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_133(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_133(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_133(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_133(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_133(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_133(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_133(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_133(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_133(self):
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

    def test_filter_document_artifacts_133(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_133(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_133(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_133(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_133(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch134:
    def test_append_recent_task_prepends_and_dedupes_134(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_134(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew134", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_134(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_134(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_134(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_134(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_134(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_134(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_134(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_134(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_134(self):
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

    def test_filter_document_artifacts_134(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_134(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_134(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_134(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_134(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch135:
    def test_append_recent_task_prepends_and_dedupes_135(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_135(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew135", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_135(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_135(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_135(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_135(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_135(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_135(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_135(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_135(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_135(self):
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

    def test_filter_document_artifacts_135(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_135(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_135(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_135(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_135(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch136:
    def test_append_recent_task_prepends_and_dedupes_136(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_136(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew136", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_136(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_136(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_136(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_136(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_136(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_136(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_136(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_136(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_136(self):
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

    def test_filter_document_artifacts_136(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_136(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_136(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_136(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_136(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch137:
    def test_append_recent_task_prepends_and_dedupes_137(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_137(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew137", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_137(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_137(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_137(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_137(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_137(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_137(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_137(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_137(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_137(self):
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

    def test_filter_document_artifacts_137(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_137(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_137(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_137(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_137(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch138:
    def test_append_recent_task_prepends_and_dedupes_138(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_138(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew138", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_138(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_138(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_138(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_138(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_138(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_138(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_138(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_138(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_138(self):
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

    def test_filter_document_artifacts_138(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_138(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_138(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_138(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_138(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch139:
    def test_append_recent_task_prepends_and_dedupes_139(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_139(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew139", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_139(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_139(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_139(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_139(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_139(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_139(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_139(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_139(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_139(self):
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

    def test_filter_document_artifacts_139(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_139(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_139(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_139(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_139(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch140:
    def test_append_recent_task_prepends_and_dedupes_140(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_140(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew140", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_140(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_140(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_140(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_140(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_140(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_140(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_140(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_140(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_140(self):
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

    def test_filter_document_artifacts_140(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_140(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_140(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_140(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_140(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch141:
    def test_append_recent_task_prepends_and_dedupes_141(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_141(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew141", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_141(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_141(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_141(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_141(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_141(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_141(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_141(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_141(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_141(self):
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

    def test_filter_document_artifacts_141(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_141(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_141(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_141(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_141(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch142:
    def test_append_recent_task_prepends_and_dedupes_142(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_142(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew142", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_142(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_142(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_142(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_142(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_142(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_142(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_142(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_142(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_142(self):
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

    def test_filter_document_artifacts_142(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_142(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_142(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_142(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_142(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch143:
    def test_append_recent_task_prepends_and_dedupes_143(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_143(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew143", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_143(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_143(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_143(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_143(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_143(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_143(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_143(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_143(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_143(self):
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

    def test_filter_document_artifacts_143(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_143(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_143(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_143(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_143(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch144:
    def test_append_recent_task_prepends_and_dedupes_144(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_144(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew144", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_144(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_144(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_144(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_144(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_144(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_144(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_144(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_144(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_144(self):
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

    def test_filter_document_artifacts_144(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_144(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_144(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_144(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_144(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch145:
    def test_append_recent_task_prepends_and_dedupes_145(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_145(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew145", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_145(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_145(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_145(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_145(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_145(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_145(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_145(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_145(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_145(self):
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

    def test_filter_document_artifacts_145(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_145(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_145(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_145(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_145(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch146:
    def test_append_recent_task_prepends_and_dedupes_146(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_146(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew146", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_146(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_146(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_146(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_146(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_146(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_146(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_146(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_146(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_146(self):
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

    def test_filter_document_artifacts_146(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_146(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_146(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_146(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_146(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch147:
    def test_append_recent_task_prepends_and_dedupes_147(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_147(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew147", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_147(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_147(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_147(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_147(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_147(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_147(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_147(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_147(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_147(self):
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

    def test_filter_document_artifacts_147(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_147(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_147(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_147(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_147(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch148:
    def test_append_recent_task_prepends_and_dedupes_148(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_148(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew148", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_148(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_148(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_148(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_148(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_148(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_148(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_148(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_148(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_148(self):
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

    def test_filter_document_artifacts_148(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_148(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_148(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_148(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_148(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch149:
    def test_append_recent_task_prepends_and_dedupes_149(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_149(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew149", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_149(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_149(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_149(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_149(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_149(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_149(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_149(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_149(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_149(self):
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

    def test_filter_document_artifacts_149(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_149(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_149(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_149(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_149(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch150:
    def test_append_recent_task_prepends_and_dedupes_150(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_150(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew150", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_150(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_150(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_150(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_150(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_150(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_150(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_150(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_150(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_150(self):
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

    def test_filter_document_artifacts_150(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_150(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_150(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_150(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_150(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch151:
    def test_append_recent_task_prepends_and_dedupes_151(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_151(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew151", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_151(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_151(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_151(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_151(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_151(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_151(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_151(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_151(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_151(self):
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

    def test_filter_document_artifacts_151(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_151(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_151(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_151(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_151(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch152:
    def test_append_recent_task_prepends_and_dedupes_152(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_152(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew152", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_152(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_152(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_152(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_152(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_152(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_152(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_152(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_152(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_152(self):
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

    def test_filter_document_artifacts_152(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_152(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_152(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_152(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_152(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch153:
    def test_append_recent_task_prepends_and_dedupes_153(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_153(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew153", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_153(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_153(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_153(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_153(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_153(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_153(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_153(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_153(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_153(self):
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

    def test_filter_document_artifacts_153(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_153(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_153(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_153(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_153(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch154:
    def test_append_recent_task_prepends_and_dedupes_154(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_154(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew154", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_154(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_154(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_154(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_154(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_154(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_154(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_154(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_154(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_154(self):
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

    def test_filter_document_artifacts_154(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_154(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_154(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_154(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_154(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch155:
    def test_append_recent_task_prepends_and_dedupes_155(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_155(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew155", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_155(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_155(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_155(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_155(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_155(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_155(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_155(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_155(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_155(self):
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

    def test_filter_document_artifacts_155(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_155(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_155(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_155(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_155(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch156:
    def test_append_recent_task_prepends_and_dedupes_156(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_156(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew156", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_156(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_156(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_156(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_156(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_156(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_156(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_156(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_156(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_156(self):
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

    def test_filter_document_artifacts_156(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_156(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_156(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_156(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_156(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch157:
    def test_append_recent_task_prepends_and_dedupes_157(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_157(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew157", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_157(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_157(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_157(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_157(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_157(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_157(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_157(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_157(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_157(self):
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

    def test_filter_document_artifacts_157(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_157(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_157(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_157(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_157(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch158:
    def test_append_recent_task_prepends_and_dedupes_158(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_158(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew158", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_158(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_158(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_158(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_158(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_158(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_158(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_158(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_158(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_158(self):
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

    def test_filter_document_artifacts_158(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_158(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_158(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_158(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_158(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch159:
    def test_append_recent_task_prepends_and_dedupes_159(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_159(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew159", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_159(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_159(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_159(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_159(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_159(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_159(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_159(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_159(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_159(self):
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

    def test_filter_document_artifacts_159(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_159(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_159(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_159(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_159(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch160:
    def test_append_recent_task_prepends_and_dedupes_160(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_160(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew160", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_160(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_160(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_160(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_160(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_160(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_160(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_160(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_160(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_160(self):
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

    def test_filter_document_artifacts_160(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_160(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_160(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_160(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_160(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch161:
    def test_append_recent_task_prepends_and_dedupes_161(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_161(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew161", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_161(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_161(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_161(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_161(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_161(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_161(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_161(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_161(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_161(self):
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

    def test_filter_document_artifacts_161(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_161(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_161(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_161(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_161(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch162:
    def test_append_recent_task_prepends_and_dedupes_162(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_162(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew162", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_162(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_162(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_162(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_162(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_162(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_162(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_162(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_162(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_162(self):
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

    def test_filter_document_artifacts_162(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_162(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_162(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_162(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_162(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


class TestUiRegressionBatch163:
    def test_append_recent_task_prepends_and_dedupes_163(self):
        recent = [{"task_id": "t1", "label": "old", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"}]
        out = append_recent_task(recent, task_id="t1", label="new", origin="pipeline", max_items=10)
        assert out[0]["label"] == "new"
        assert len([x for x in out if x["task_id"] == "t1"]) == 1

    def test_append_recent_task_respects_max_items_163(self):
        recent = [{"task_id": f"t{n}", "label": "x", "origin": "pipeline", "queued_at": "2026-01-01T00:00:00"} for n in range(30)]
        out = append_recent_task(recent, task_id="tnew163", label="new", origin="pipeline", max_items=10)
        assert len(out) == 10

    def test_build_matrix_query_params_full_163(self):
        p = build_matrix_query_params(page_size=50, scope_type="disease", scope_id=" RA ", model_version_id=3, molecule_from_id=11)
        assert p["page"] == 1
        assert p["scope_type"] == "disease"
        assert p["scope_id"] == "RA"
        assert p["model_version_id"] == 3
        assert p["molecule_from_id"] == 11

    def test_build_matrix_query_params_minimal_163(self):
        p = build_matrix_query_params(page_size=20, scope_type="global", scope_id=" ", model_version_id=0, molecule_from_id=0)
        assert p["page_size"] == 20
        assert "scope_id" not in p
        assert "model_version_id" not in p
        assert "molecule_from_id" not in p

    def test_build_matrix_cell_detail_params_optional_163(self):
        p = build_matrix_cell_detail_params(molecule_from_id=1, molecule_to_id=2, scope_type="global", model_version_id=0)
        assert p["molecule_from_id"] == 1
        assert p["molecule_to_id"] == 2
        assert "model_version_id" not in p

    def test_build_bulk_approve_evidence_ids_dedupe_163(self):
        ids = build_bulk_approve_evidence_ids("1, 2, 2, 3", [3, 4, 4, 5])
        assert ids == [1, 2, 3, 4, 5]

    def test_resolve_helpers_priority_selected_163(self):
        assert resolve_review_target_id(10, 20) == 20
        assert resolve_history_target_id(10, 20) == 20
        assert resolve_document_id(10, 20) == 20
        assert resolve_output_id(10, 20) == 20
        assert resolve_artifact_id(10, 20) == 20
        assert resolve_entity_id(10, 20) == 20
        assert resolve_task_id(" manual ", "queued") == "queued"

    def test_resolve_task_id_falls_back_to_trimmed_manual_163(self):
        assert resolve_task_id("  abc-123  ", None) == "abc-123"

    def test_recent_task_filters_and_search_163(self):
        items = [
            {"origin": "pipeline", "label": "sync_full", "queued_at": "2026-01-01T00:00:01"},
            {"origin": "outputs", "label": "output_generate", "queued_at": "2026-01-01T00:00:02"},
        ]
        f = filter_recent_tasks(items, "pipeline")
        s = search_recent_tasks(items, "output")
        assert len(f) == 1
        assert len(s) == 1

    def test_recent_task_sort_orders_163(self):
        items = [
            {"queued_at": "2026-01-01T00:00:01"},
            {"queued_at": "2026-01-01T00:00:03"},
            {"queued_at": "2026-01-01T00:00:02"},
        ]
        newest = sort_recent_tasks(items, "newest")
        oldest = sort_recent_tasks(items, "oldest")
        assert newest[0]["queued_at"] == "2026-01-01T00:00:03"
        assert oldest[0]["queued_at"] == "2026-01-01T00:00:01"

    def test_document_filters_and_sort_163(self):
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

    def test_filter_document_artifacts_163(self):
        arts = [
            {"artifact_type": "html", "id": 1},
            {"artifact_type": "pdf", "id": 2},
        ]
        out = filter_document_artifacts(arts, "pdf")
        assert len(out) == 1
        assert out[0]["id"] == 2

    def test_filter_document_sections_by_title_and_fragment_163(self):
        sections = [
            {"section_title": "Lechenie", "fragments": [{"fragment_text": "Metotreksat"}]},
            {"section_title": "Diagnostika", "fragments": [{"fragment_text": "SRB"}]},
        ]
        by_title = filter_document_sections(sections, "lechenie")
        by_fragment = filter_document_sections(sections, "srb")
        assert len(by_title) == 1
        assert len(by_fragment) == 1
        assert by_fragment[0]["section_title"] == "Diagnostika"

    def test_filter_pipeline_runs_163(self):
        runs = [
            {"status": "queued"},
            {"status": "running"},
            {"status": "completed"},
        ]
        out = filter_pipeline_runs(runs, "running")
        assert len(out) == 1
        assert out[0]["status"] == "running"

    def test_split_frontmatter_parses_valid_payload_163(self):
        text = "---\ntitle: demo\n---\n\nBody text"
        fm, body = _split_frontmatter(text)
        assert "title: demo" in (fm or "")
        assert body.startswith("Body text")

    def test_split_frontmatter_handles_plain_markdown_163(self):
        text = "No frontmatter here"
        fm, body = _split_frontmatter(text)
        assert fm is None
        assert body == text


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

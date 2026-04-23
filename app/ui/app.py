"""CR Intelligence Platform — Streamlit Admin UI."""

import httpx
import pandas as pd
import streamlit as st

API_BASE = "http://app:8000"


def _split_frontmatter(content_md: str | None) -> tuple[str | None, str]:
    if not content_md:
        return None, ""
    if not content_md.startswith("---\n"):
        return None, content_md
    parts = content_md[4:].split("\n---\n", 1)
    if len(parts) != 2:
        return None, content_md
    frontmatter, body = parts
    return frontmatter, body.lstrip("\n")


def render_kb_artifact_detail(detail: dict) -> None:
    st.markdown(f"**{detail.get('title', 'KB Artifact')}**")
    meta1, meta2, meta3, meta4 = st.columns(4)
    meta1.metric("Artifact ID", detail.get("id"))
    meta2.metric("Type", detail.get("artifact_type") or "n/a")
    meta3.metric("Status", detail.get("status") or "n/a")
    meta4.metric("Claims", len(detail.get("claims") or []))

    if detail.get("summary"):
        st.caption(detail.get("summary"))

    if detail.get("manifest_json"):
        with st.expander("Manifest", expanded=False):
            st.json(detail.get("manifest_json"))

    source_links = detail.get("source_links") or []
    if source_links:
        st.markdown("**Source Links**")
        st.dataframe(pd.DataFrame(source_links), width="stretch", hide_index=True)

    claims = detail.get("claims") or []
    if claims:
        st.markdown("**Claims**")
        claim_rows = []
        for claim in claims:
            claim_rows.append(
                {
                    "id": claim.get("id"),
                    "type": claim.get("claim_type"),
                    "confidence": claim.get("confidence"),
                    "review": claim.get("review_status"),
                    "text": claim.get("claim_text"),
                }
            )
        st.dataframe(pd.DataFrame(claim_rows), width="stretch", hide_index=True)

    frontmatter, body = _split_frontmatter(detail.get("content_md"))
    if frontmatter:
        with st.expander("Frontmatter", expanded=True):
            st.code(frontmatter, language="yaml")
    if body:
        with st.expander("Markdown Body", expanded=True):
            st.code(body, language="markdown")

    with st.expander("Raw Payload", expanded=False):
        st.json(detail)


def render_output_detail(detail: dict) -> None:
    st.markdown(f"**{detail.get('title', 'Output')}**")
    meta1, meta2, meta3, meta4 = st.columns(4)
    meta1.metric("Output ID", detail.get("id"))
    meta2.metric("Type", detail.get("output_type") or "n/a")
    meta3.metric("File-Back", detail.get("file_back_status") or "n/a")
    meta4.metric("Artifact", detail.get("artifact_id") or "none")

    if detail.get("review_status") or detail.get("generator_version"):
        st.caption(
            f"review={detail.get('review_status') or 'n/a'} | "
            f"generator={detail.get('generator_version') or 'n/a'}"
        )

    if detail.get("scope_json"):
        with st.expander("Scope", expanded=False):
            st.json(detail.get("scope_json"))

    if detail.get("file_pointer"):
        st.code(detail.get("file_pointer"), language="text")

    with st.expander("Raw Payload", expanded=False):
        st.json(detail)


def render_entity_detail(detail: dict) -> None:
    st.caption(f"Entity #{detail.get('id')}")
    meta1, meta2, meta3 = st.columns(3)
    meta1.metric("Type", detail.get("entity_type") or "n/a")
    meta2.metric("Status", detail.get("status") or "n/a")
    meta3.metric("Aliases", len(detail.get("aliases_json") or {}))
    st.subheader(detail.get("canonical_name") or "Untitled entity")

    aliases = detail.get("aliases_json") or {}
    if aliases:
        with st.expander("Aliases", expanded=False):
            st.json(aliases)

    external_refs = detail.get("external_refs_json") or {}
    if external_refs:
        with st.expander("External Refs", expanded=False):
            st.json(external_refs)

    with st.expander("Raw Payload", expanded=False):
        st.json(detail)


def api_get(
    path: str,
    params: dict | None = None,
    allow_statuses: set[int] | None = None,
) -> dict | list | None:
    """Make GET request to backend API."""
    try:
        resp = httpx.get(f"{API_BASE}{path}", params=params, timeout=30)
        if allow_statuses and resp.status_code in allow_statuses:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        st.error(f"API error: {e}")
        return None


def api_post(path: str, json: dict | None = None) -> dict | None:
    """Make POST request to backend API."""
    try:
        resp = httpx.post(f"{API_BASE}{path}", json=json, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        st.error(f"API error: {e}")
        return None


# --- Page: Dashboard ---

def page_dashboard():
    st.header("Dashboard")

    col1, col2, col3, col4, col5 = st.columns(5)

    # Documents stats
    docs = api_get("/documents", {"page_size": 1})
    if docs:
        col1.metric("Documents", docs.get("total", 0))

    # Matrix stats
    matrix = api_get("/matrix", {"page_size": 1})
    if matrix:
        col2.metric("Matrix Cells", matrix.get("total", 0))

    # Pipeline runs
    runs = api_get("/runs", {"page_size": 1})
    if runs:
        col3.metric("Pipeline Runs", runs.get("total", 0))

    # Output releases
    outputs = api_get("/outputs", {"page_size": 1})
    if outputs:
        col4.metric("Outputs", outputs.get("total", 0))

    # Knowledge artifacts
    kb_artifacts = api_get("/kb/artifacts", {"page_size": 1})
    if kb_artifacts:
        col5.metric("KB Artifacts", kb_artifacts.get("total", 0))

    # Health check
    st.subheader("System Health")
    health = api_get("/health")
    if health:
        status = health.get("status", "unknown")
        if status == "ok":
            st.success("All systems operational")
        else:
            st.warning(f"Status: {status}")
            if health.get("db_error"):
                st.error(f"DB: {health['db_error']}")

    st.subheader("Release Gate Snapshot")

    snapshot_col1, snapshot_col2 = st.columns(2)

    latest_runs = api_get("/runs", {"page_size": 5})
    latest_outputs = api_get("/outputs", {"page_size": 5})
    active_model = api_get("/matrix/models/active", allow_statuses={404})
    kb_master = api_get("/kb/indexes/master", allow_statuses={404})

    with snapshot_col1:
        st.markdown("**Latest Pipeline Runs**")
        if isinstance(latest_runs, dict) and latest_runs.get("items"):
            run_rows = []
            for item in latest_runs.get("items", [])[:5]:
                run_rows.append(
                    {
                        "id": item.get("id"),
                        "status": item.get("status"),
                        "discovered": item.get("discovered_count"),
                        "fetched": item.get("fetched_count"),
                        "finished_at": item.get("finished_at"),
                    }
                )
            st.dataframe(pd.DataFrame(run_rows), width="stretch", hide_index=True)
        else:
            st.info("No pipeline runs available")

        st.markdown("**Latest Outputs**")
        if isinstance(latest_outputs, dict) and latest_outputs.get("items"):
            output_rows = []
            for item in latest_outputs.get("items", [])[:5]:
                output_rows.append(
                    {
                        "id": item.get("id"),
                        "type": item.get("output_type"),
                        "status": item.get("file_back_status") or "n/a",
                        "title": item.get("title"),
                    }
                )
            st.dataframe(pd.DataFrame(output_rows), width="stretch", hide_index=True)
        else:
            st.info("No outputs available")

    with snapshot_col2:
        st.markdown("**Release-Critical Operator Surfaces**")
        if isinstance(active_model, dict):
            st.success(
                f"Active scoring model: #{active_model.get('id')} {active_model.get('version_label')}"
            )
        else:
            st.warning("No active scoring model")

        if isinstance(kb_master, dict):
            st.success(
                "KB master index available: "
                f"artifact #{kb_master.get('artifact_id')} ({kb_master.get('format')})"
            )
        else:
            st.warning("KB master index unavailable")

        st.caption("Quick operator checks")
        st.code(
            "GET /health\n"
            "GET /outputs?page=1\n"
            "GET /kb/indexes/master\n"
            "GET /matrix/models/active",
            language="text",
        )


# --- Page: Documents ---

def page_documents():
    st.header("Document Registry")

    col1, col2 = st.columns(2)
    search = col1.text_input("Search", "")
    specialty = col2.text_input("Specialty filter", "")

    params = {"page": 1, "page_size": 50}
    if search:
        params["search"] = search
    if specialty:
        params["specialty"] = specialty

    data = api_get("/documents", params)
    if not data:
        return

    items = data.get("items", [])
    if not items:
        st.info("No documents found")
        return

    df = pd.DataFrame(items)
    display_cols = ["id", "title", "specialty", "status", "external_id"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], width="stretch")

    # Document detail
    st.subheader("Document Detail")
    doc_id = st.number_input("Document ID", min_value=1, step=1)
    if st.button("Load Document"):
        detail = api_get(f"/documents/{doc_id}")
        if detail:
            st.json(detail)

        artifacts = api_get(f"/documents/{doc_id}/artifacts")
        st.subheader("Raw Source Artifacts")
        if isinstance(artifacts, dict) and artifacts.get("artifacts"):
            for artifact in artifacts.get("artifacts", []):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(
                    f"#{artifact.get('id')} {artifact.get('artifact_type')} "
                    f"({artifact.get('content_type') or 'application/octet-stream'})"
                )
                col2.link_button("Download", f"{API_BASE}{artifact.get('download_url')}")
                col3.link_button("Preview", f"{API_BASE}{artifact.get('preview_url')}")
        else:
            st.info("No valid raw artifacts available for current version")

        content = api_get(f"/documents/{doc_id}/content")
        if content:
            sections = content.get("sections", [])
            for sec in sections:
                with st.expander(sec.get("section_title", "Section")):
                    fragments = sec.get("fragments", [])
                    for frag in fragments:
                        st.text(frag.get("fragment_text", "")[:500])


# --- Page: Pipeline ---

def page_pipeline():
    st.header("Pipeline Management")

    col1, col2 = st.columns(2)
    if col1.button("Run Full Sync", type="primary"):
        result = api_post("/sync/full")
        if result:
            st.success(f"Pipeline run started: ID {result.get('run_id')}")

    if col2.button("Run Incremental Sync"):
        result = api_post("/sync/incremental")
        if result:
            st.success(f"Pipeline run started: ID {result.get('run_id')}")

    # Recent runs
    st.subheader("Recent Pipeline Runs")
    runs = api_get("/runs", {"page_size": 20})
    if runs:
        items = runs.get("items", [])
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, width="stretch")
        else:
            st.info("No pipeline runs yet")


# --- Page: Matrix ---

def page_matrix():
    st.header("Substitution Matrix")

    col1, col2 = st.columns(2)
    scope_type = col1.selectbox("Scope", ["global", "disease"])
    page_size = col2.number_input("Page size", min_value=10, max_value=500, value=50)

    params = {"page": 1, "page_size": page_size}
    if scope_type:
        params["scope_type"] = scope_type

    data = api_get("/matrix", params)
    if not data:
        return

    items = data.get("items", [])
    if not items:
        st.info("No matrix cells found")
        return

    df = pd.DataFrame(items)
    st.dataframe(df, width="stretch")

    # Export
    st.subheader("Export Matrix")
    fmt = st.selectbox("Format", ["csv", "jsonl"])
    if st.button("Download"):
        st.info(f"Use API endpoint: GET /matrix/export?format={fmt}")

    # Cell detail
    st.subheader("Cell Detail")
    col1, col2 = st.columns(2)
    mol_from = col1.number_input("Molecule From ID", min_value=1, step=1)
    mol_to = col2.number_input("Molecule To ID", min_value=1, step=1)
    if st.button("Load Cell Detail"):
        detail = api_get("/matrix/cell", {"molecule_from_id": mol_from, "molecule_to_id": mol_to})
        if detail:
            st.json(detail)


# --- Page: Reviews ---

def page_reviews():
    st.header("Reviewer Queue")

    stats = api_get("/review/stats")
    if isinstance(stats, dict):
        counts = stats.get("counts", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Auto", counts.get("auto", 0))
        col2.metric("Approved", counts.get("approved", 0))
        col3.metric("Rejected", counts.get("rejected", 0))

    st.subheader("Queue")
    queue_document_version_id = st.number_input(
        "Queue Document Version ID",
        min_value=0,
        step=1,
        help="0 means no document filter",
    )
    queue_params = {"status": "auto", "page_size": 50}
    if queue_document_version_id > 0:
        queue_params["document_version_id"] = queue_document_version_id
    queue = api_get("/review/queue", queue_params)
    if isinstance(queue, dict):
        items = queue.get("items", [])
        if items:
            st.dataframe(pd.DataFrame(items), width="stretch")
        else:
            st.info("No evidence awaiting review")

    # Review history
    st.subheader("Recent Review Actions")
    history_target_id = st.number_input(
        "History Target ID",
        min_value=0,
        step=1,
        help="0 means no target filter",
    )
    history_params = {"page_size": 50}
    if history_target_id > 0:
        history_params["target_id"] = history_target_id
    reviews = api_get("/review/history", history_params)
    if isinstance(reviews, dict):
        items = reviews.get("items", [])
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, width="stretch")
        else:
            st.info("No review actions yet")

    st.subheader("Bulk Approve")
    with st.form("bulk_review_form"):
        bulk_ids = st.text_input("Evidence IDs (comma-separated)")
        bulk_author = st.text_input("Bulk Approve Author")
        st.caption("Use the filtered queue above to identify evidence IDs for bulk approval.")
        if st.form_submit_button("Bulk Approve"):
            evidence_ids = [int(item.strip()) for item in bulk_ids.split(",") if item.strip()]
            if not evidence_ids:
                st.warning("Enter at least one evidence ID")
            else:
                result = api_post(
                    "/review/bulk-approve",
                    {"evidence_ids": evidence_ids, "author": bulk_author},
                )
                if result:
                    st.success(f"Approved {result.get('approved_count', 0)} evidence items")

    # Submit review
    st.subheader("Submit Review")
    with st.form("review_form"):
        target_type = st.selectbox("Target Type", ["pair_evidence"])
        target_id = st.number_input("Target ID", min_value=1, step=1)
        action = st.selectbox("Action", ["approve", "reject", "override"])
        reason = st.text_area("Reason")
        author = st.text_input("Author")
        override_score = None
        if action == "override":
            override_score = st.number_input("Override Score", min_value=0.0, max_value=1.0, step=0.01)

        if st.form_submit_button("Submit"):
            payload = {
                "target_type": target_type,
                "target_id": target_id,
                "action": action,
                "reason": reason,
                "author": author,
            }
            if action == "override":
                payload["new_value_json"] = {"final_fragment_score": override_score}
            result = api_post("/review", payload)
            if result:
                st.success("Review submitted")


# --- Page: Scoring Models ---

def page_scoring_models():
    st.header("Scoring Models")

    models = api_get("/matrix/models")
    if isinstance(models, list) and models:
        overview = api_get("/matrix/models/overview")
        if isinstance(overview, list) and overview:
            overview_rows = []
            for item in overview:
                readiness = item.get("readiness", {})
                overview_rows.append(
                    {
                        "model_version_id": item.get("model_version_id"),
                        "version_label": item.get("version_label"),
                        "is_active": item.get("is_active"),
                        "ready": readiness.get("ready"),
                        "cell_count": readiness.get("cell_count"),
                        "pcs_count": readiness.get("pcs_count"),
                        "low_confidence_ratio": readiness.get("low_confidence_ratio"),
                    }
                )
            st.dataframe(pd.DataFrame(overview_rows), width="stretch")
        else:
            st.dataframe(pd.DataFrame(models), width="stretch")

        active_model = api_get("/matrix/models/active", allow_statuses={404})
        if isinstance(active_model, dict):
            st.success(
                f"Active model: #{active_model.get('id')} {active_model.get('version_label')}"
            )

        model_options = {
            f"#{model['id']} {model['version_label']}": model["id"] for model in models
        }
        selected_label = st.selectbox("Selected Model", list(model_options.keys()))
        selected_model_id = model_options[selected_label]

        summary = api_get(f"/matrix/models/{selected_model_id}/summary")
        if isinstance(summary, dict):
            readiness = summary.get("readiness", {})
            col1, col2, col3 = st.columns(3)
            col1.metric("Ready", "yes" if readiness.get("ready") else "no")
            col2.metric("Cells", readiness.get("cell_count", 0))
            col3.metric("Pair Scores", readiness.get("pcs_count", 0))

        st.subheader("Model Actions")
        with st.form("model_refresh_form"):
            refresh_scope_type = st.selectbox("Refresh Scope Type", ["global"], key="refresh_scope_type")
            refresh_scope_id = st.text_input("Refresh Scope ID", value="", key="refresh_scope_id")
            if st.form_submit_button("Refresh Model"):
                payload = {
                    "scope_type": refresh_scope_type,
                    "scope_id": refresh_scope_id or None,
                }
                result = api_post(f"/matrix/models/{selected_model_id}/refresh", payload)
                if result:
                    st.success(
                        f"Refreshed: {result.get('pair_context_scores', 0)} pair scores, "
                        f"{result.get('matrix_cells', 0)} matrix cells"
                    )

        with st.form("model_activate_form"):
            activate_author = st.text_input("Activation Author", key="activate_author")
            activate_force = st.checkbox("Force Activate", value=False)
            if st.form_submit_button("Activate Model"):
                result = api_post(
                    f"/matrix/models/{selected_model_id}/activate",
                    {"author": activate_author, "force": activate_force},
                )
                if result:
                    st.success(f"Activated model {result.get('version_label')}")

        st.subheader("Model Diff")
        diff_options = {
            f"#{model['id']} {model['version_label']}": model["id"] for model in models
        }
        diff_left = st.selectbox("Old Version", list(diff_options.keys()), key="diff_left")
        diff_right = st.selectbox("New Version", list(diff_options.keys()), key="diff_right")
        if st.button("Load Diff"):
            diff = api_get(
                "/matrix/models/diff",
                {
                    "old_version_id": diff_options[diff_left],
                    "new_version_id": diff_options[diff_right],
                },
            )
            if isinstance(diff, dict):
                st.json(diff)
    else:
        st.info("No scoring models defined")

    # Create new model
    st.subheader("Create Scoring Model Version")
    with st.form("model_form"):
        label = st.text_input("Version Label", "v1.0")
        weights_str = st.text_area(
            "Weights JSON",
            '{"role": 0.2, "text": 0.25, "population": 0.15, "parity": 0.15, "practical": 0.1, "penalty": 0.15}',
        )

        if st.form_submit_button("Create"):
            import json
            try:
                weights = json.loads(weights_str)
            except json.JSONDecodeError:
                st.error("Invalid JSON")
                return

            result = api_post("/matrix/models", {"version_label": label, "weights_json": weights})
            if result:
                st.success(f"Model created: ID {result.get('id')}")


# --- Page: Outputs ---

def page_outputs():
    st.header("Outputs")

    out_col1, out_col2, out_col3, out_col4, out_col5 = st.columns(5)
    output_type_filter = out_col1.selectbox("Output Type Filter", ["", "memo"], index=0)
    file_back_filter = out_col2.selectbox(
        "File-Back Filter",
        ["", "accepted", "rejected", "needs_review"],
        index=0,
    )
    review_status_filter = out_col3.selectbox(
        "Review Status Filter",
        ["", "draft", "auto", "needs_review", "approved", "rejected"],
        index=0,
    )
    generator_version_filter = out_col4.text_input("Generator Version Filter")
    output_artifact_id = out_col5.number_input(
        "Artifact ID Filter",
        min_value=0,
        step=1,
        help="0 means no artifact filter",
    )
    output_search = st.text_input("Output Search")
    released_only = st.checkbox("Released Outputs Only")
    params = {"page_size": 50}
    if output_type_filter:
        params["output_type"] = output_type_filter
    if file_back_filter:
        params["file_back_status"] = file_back_filter
    if review_status_filter:
        params["review_status"] = review_status_filter
    if generator_version_filter:
        params["generator_version"] = generator_version_filter
    if released_only:
        params["released_only"] = True
    if output_artifact_id > 0:
        params["artifact_id"] = output_artifact_id
    if output_search:
        params["search"] = output_search

    outputs = api_get("/outputs", params)
    if isinstance(outputs, dict):
        items = outputs.get("items", [])
        if items:
            st.dataframe(pd.DataFrame(items), width="stretch")
        else:
            st.info("No outputs available")

    st.subheader("Output Detail")
    detail_output_id = st.number_input("Detail Output ID", min_value=1, step=1, key="detail_output_id")
    if st.button("Load Output Detail"):
        detail = api_get(f"/outputs/{detail_output_id}")
        if detail:
            render_output_detail(detail)
            artifact_id = detail.get("artifact_id")
            if artifact_id:
                st.success(f"Linked KB artifact: #{artifact_id}")
                if st.button("Load Linked Artifact", key=f"load_output_artifact_{artifact_id}"):
                    artifact = api_get(f"/kb/artifacts/{artifact_id}")
                    if artifact:
                        render_kb_artifact_detail(artifact)

    st.subheader("Generate Output")
    with st.form("output_generate_form"):
        output_type = st.selectbox("Output Type", ["memo"])
        title = st.text_input("Title")
        if st.form_submit_button("Queue Generation"):
            result = api_post(
                "/outputs/generate",
                {"output_type": output_type, "title": title or None, "scope_json": None},
            )
            if result:
                st.success(f"Generation queued: {result.get('task_id')}")

    st.subheader("File Back Output")
    with st.form("output_file_back_form"):
        output_id = st.number_input("Output ID", min_value=1, step=1)
        file_back_status = st.selectbox("File Back Status", ["accepted", "rejected", "needs_review"])
        if st.form_submit_button("Queue File Back"):
            result = api_post(
                f"/outputs/file-back/{output_id}",
                {"file_back_status": file_back_status},
            )
            if result:
                st.success(f"File-back queued: {result.get('task_id')}")


# --- Page: Knowledge Base ---

def page_kb():
    st.header("Knowledge Base")

    col1, col2 = st.columns(2)
    if col1.button("Compile KB"):
        result = api_post("/kb/compile")
        if result:
            st.success(f"KB compile queued: {result.get('task_id')}")

    if col2.button("Lint KB"):
        result = api_post("/kb/lint")
        if result:
            st.success(f"KB lint queued: {result.get('task_id')}")

    st.subheader("Master Index")
    master_index = api_get("/kb/indexes/master", allow_statuses={404})
    if isinstance(master_index, dict):
        if master_index.get("artifact_id"):
            st.success(
                f"artifact #{master_index.get('artifact_id')} {master_index.get('canonical_slug')}"
            )
            if master_index.get("manifest_json"):
                with st.expander("Master Manifest", expanded=False):
                    st.json(master_index.get("manifest_json"))
        else:
            st.info(master_index.get("message") or "No master index artifact yet")

    st.subheader("Artifacts")
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
    artifact_type_filter = filter_col1.selectbox(
        "Artifact Type Filter",
        ["", "source_digest", "entity_page", "glossary_term", "open_question", "master_index"],
        index=0,
        key="kb_artifact_type_filter",
    )
    artifact_status_filter = filter_col2.selectbox(
        "Artifact Status Filter",
        ["", "draft", "active", "archived"],
        index=0,
        key="kb_artifact_status_filter",
    )
    artifact_review_filter = filter_col3.selectbox(
        "Artifact Review Filter",
        ["", "draft", "auto", "needs_review", "approved", "rejected"],
        index=0,
        key="kb_artifact_review_filter",
    )
    artifact_generator_filter = filter_col4.text_input(
        "Artifact Generator Filter",
        key="kb_artifact_generator_filter",
    )
    artifact_search = filter_col5.text_input("Artifact Search", key="kb_artifact_search")
    artifact_params = {"page_size": 50}
    if artifact_type_filter:
        artifact_params["artifact_type"] = artifact_type_filter
    if artifact_status_filter:
        artifact_params["status"] = artifact_status_filter
    if artifact_review_filter:
        artifact_params["review_status"] = artifact_review_filter
    if artifact_generator_filter:
        artifact_params["generator_version"] = artifact_generator_filter
    if artifact_search:
        artifact_params["search"] = artifact_search

    artifacts = api_get("/kb/artifacts", artifact_params)
    if isinstance(artifacts, dict):
        items = artifacts.get("items", [])
        if items:
            st.dataframe(pd.DataFrame(items), width="stretch")
        else:
            st.info("No KB artifacts available")

    st.subheader("Artifact Detail")
    artifact_id = st.number_input("Artifact ID", min_value=1, step=1, key="artifact_id")
    if st.button("Load Artifact"):
        detail = api_get(f"/kb/artifacts/{artifact_id}")
        if detail:
            render_kb_artifact_detail(detail)

    st.subheader("Entities")
    entity_col1, entity_col2, entity_col3 = st.columns(3)
    entity_type_filter = entity_col1.selectbox(
        "Entity Type Filter",
        ["", "document", "molecule"],
        index=0,
        key="kb_entity_type_filter",
    )
    entity_status_filter = entity_col2.selectbox(
        "Entity Status Filter",
        ["", "active", "draft", "archived"],
        index=0,
        key="kb_entity_status_filter",
    )
    entity_search = entity_col3.text_input("Entity Search", key="kb_entity_search")
    entity_params = {"page_size": 50}
    if entity_type_filter:
        entity_params["entity_type"] = entity_type_filter
    if entity_status_filter:
        entity_params["status"] = entity_status_filter
    if entity_search:
        entity_params["search"] = entity_search

    entities = api_get("/kb/entities", entity_params)
    if isinstance(entities, dict):
        items = entities.get("items", [])
        if items:
            entity_rows = []
            for item in items:
                entity_rows.append(
                    {
                        "id": item.get("id"),
                        "type": item.get("entity_type"),
                        "canonical_name": item.get("canonical_name"),
                        "status": item.get("status"),
                        "alias_count": len(item.get("aliases_json") or {}),
                        "external_ref_count": len(item.get("external_refs_json") or {}),
                    }
                )
            st.dataframe(pd.DataFrame(entity_rows), width="stretch", hide_index=True)
        else:
            st.info("No KB entities available")

    st.subheader("Entity Detail")
    entity_id = st.number_input("Entity ID", min_value=1, step=1, key="kb_entity_id")
    if st.button("Load Entity"):
        entity_detail = api_get(f"/kb/entities/{entity_id}")
        if entity_detail:
            render_entity_detail(entity_detail)

    st.subheader("Conflicts")
    conflict_artifact_id = st.number_input(
        "Conflict Artifact ID Filter",
        min_value=0,
        step=1,
        key="kb_conflict_artifact_id",
        help="0 means no artifact filter",
    )
    conflict_params = None
    if conflict_artifact_id > 0:
        conflict_params = {"artifact_id": conflict_artifact_id}
    conflicts = api_get("/kb/conflicts", conflict_params)
    if isinstance(conflicts, list):
        if conflicts:
            conflict_rows = []
            for item in conflicts:
                conflict_rows.append(
                    {
                        "conflict_group_id": item.get("conflict_group_id"),
                        "claim_count": item.get("claim_count"),
                        "claim_ids": ", ".join(str(claim_id) for claim_id in item.get("claim_ids", [])),
                        "claim_previews": "\n\n".join(item.get("claim_previews", [])),
                    }
                )
            st.dataframe(pd.DataFrame(conflict_rows), width="stretch", hide_index=True)
        else:
            st.info("No KB conflicts detected")

    st.subheader("Claims")
    claim_col1, claim_col2, claim_col3, claim_col4 = st.columns(4)
    claim_artifact_id = claim_col1.number_input(
        "Claim Artifact ID Filter",
        min_value=0,
        step=1,
        key="kb_claim_artifact_id",
        help="0 means no artifact filter",
    )
    claim_type_filter = claim_col2.selectbox(
        "Claim Type Filter",
        ["", "fact", "inference", "hypothesis"],
        index=0,
        key="kb_claim_type_filter",
    )
    claim_review_filter = claim_col3.selectbox(
        "Claim Review Filter",
        ["", "auto", "needs_review", "approved", "rejected"],
        index=0,
        key="kb_claim_review_filter",
    )
    claim_page_size = claim_col4.number_input(
        "Claims Page Size",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        key="kb_claim_page_size",
    )
    claim_search = st.text_input("Claim Search", key="kb_claim_search")
    conflicted_only = st.checkbox("Conflicted Claims Only", key="kb_claim_conflicted_only")
    claim_params = {"page_size": claim_page_size}
    if claim_artifact_id > 0:
        claim_params["artifact_id"] = claim_artifact_id
    if claim_type_filter:
        claim_params["claim_type"] = claim_type_filter
    if claim_review_filter:
        claim_params["review_status"] = claim_review_filter
    if conflicted_only:
        claim_params["conflicted_only"] = True
    if claim_search:
        claim_params["search"] = claim_search
    claims = api_get("/kb/claims", claim_params)
    if isinstance(claims, dict):
        items = claims.get("items", [])
        if items:
            claim_rows = []
            for item in items:
                claim_rows.append(
                    {
                        "id": item.get("id"),
                        "artifact_id": item.get("artifact_id"),
                        "type": item.get("claim_type"),
                        "conflicted": item.get("is_conflicted"),
                        "conflict_group_id": item.get("conflict_group_id"),
                        "confidence": item.get("confidence"),
                        "review_status": item.get("review_status"),
                        "text": item.get("claim_text"),
                    }
                )
            st.dataframe(pd.DataFrame(claim_rows), width="stretch", hide_index=True)
        else:
            st.info("No KB claims available")


# --- Page: Tasks ---

def page_tasks():
    st.header("Tasks")

    task_id = st.text_input("Task ID")
    include_result = st.checkbox("Include Result", value=True)
    if st.button("Load Task Status"):
        if not task_id.strip():
            st.warning("Enter a task ID")
        else:
            status = api_get(f"/tasks/{task_id.strip()}", {"include_result": include_result})
            if status:
                st.json(status)


# --- Main ---

def main():
    st.set_page_config(page_title="CR Intelligence Platform", layout="wide")
    st.title("CR Intelligence Platform")

    pages = {
        "Dashboard": page_dashboard,
        "Documents": page_documents,
        "Pipeline": page_pipeline,
        "Matrix": page_matrix,
        "Reviews": page_reviews,
        "Scoring Models": page_scoring_models,
        "Knowledge Base": page_kb,
        "Tasks": page_tasks,
        "Outputs": page_outputs,
    }

    page = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[page]()


if __name__ == "__main__":
    main()

"""CR Intelligence Platform — Streamlit Admin UI."""

import httpx
import pandas as pd
import streamlit as st

API_BASE = "http://app:8000"


def api_get(path: str, params: dict | None = None) -> dict | list | None:
    """Make GET request to backend API."""
    try:
        resp = httpx.get(f"{API_BASE}{path}", params=params, timeout=30)
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

    col1, col2, col3 = st.columns(3)

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
    st.dataframe(df[display_cols], use_container_width=True)

    # Document detail
    st.subheader("Document Detail")
    doc_id = st.number_input("Document ID", min_value=1, step=1)
    if st.button("Load Document"):
        detail = api_get(f"/documents/{doc_id}")
        if detail:
            st.json(detail)

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
            st.dataframe(df, use_container_width=True)
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
    st.dataframe(df, use_container_width=True)

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
            st.dataframe(pd.DataFrame(items), use_container_width=True)
        else:
            st.info("No evidence awaiting review")

    # Review history
    st.subheader("Recent Review Actions")
    reviews = api_get("/review/history", {"page_size": 50})
    if isinstance(reviews, dict):
        items = reviews.get("items", [])
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
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
        df = pd.DataFrame(models)
        st.dataframe(df, use_container_width=True)

        active_model = api_get("/matrix/models/active")
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
    }

    page = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[page]()


if __name__ == "__main__":
    main()

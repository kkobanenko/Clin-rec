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

    # Review history
    st.subheader("Recent Review Actions")
    reviews = api_get("/reviews", {"page_size": 50})
    if reviews:
        items = reviews.get("items", [])
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No review actions yet")

    # Submit review
    st.subheader("Submit Review")
    with st.form("review_form"):
        target_type = st.selectbox("Target Type", ["pair_evidence", "matrix_cell"])
        target_id = st.number_input("Target ID", min_value=1, step=1)
        action = st.selectbox("Action", ["approve", "reject", "override"])
        reason = st.text_area("Reason")
        author = st.text_input("Author")

        if st.form_submit_button("Submit"):
            payload = {
                "target_type": target_type,
                "target_id": target_id,
                "action": action,
                "reason": reason,
                "author": author,
            }
            result = api_post("/review", payload)
            if result:
                st.success("Review submitted")


# --- Page: Scoring Models ---

def page_scoring_models():
    st.header("Scoring Models")

    models = api_get("/matrix/models")
    if models:
        if models:
            df = pd.DataFrame(models)
            st.dataframe(df, use_container_width=True)
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

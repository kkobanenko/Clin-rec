"""CR Intelligence Platform — Streamlit Admin UI."""

import os

import httpx
import pandas as pd
import streamlit as st

# В docker: http://app:8000; локально: http://127.0.0.1:8000 (см. CRIN_STREAMLIT_API_BASE в compose).
API_BASE = os.environ.get("CRIN_STREAMLIT_API_BASE", "http://app:8000")


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


# --- Page: Knowledge base (TZ §21) ---


def page_knowledge_base():
    st.header("Knowledge base")

    st.subheader("Master index")
    mi = api_get("/kb/indexes/master")
    if mi:
        if mi.get("artifact_id"):
            st.caption(
                f"artifact_id={mi.get('artifact_id')} slug={mi.get('canonical_slug')}"
            )
            if mi.get("manifest_json"):
                with st.expander("manifest_json"):
                    st.json(mi["manifest_json"])
            body = mi.get("content_md") or ""
            st.markdown(body if body else "*пусто*", unsafe_allow_html=False)
        else:
            st.info(mi.get("message", "Нет master_index — выполните компиляцию после корпуса."))

    st.subheader("Действия")
    c1, c2 = st.columns(2)
    if c1.button("Запустить compile_kb (Celery)"):
        r = api_post("/kb/compile")
        if r:
            tid = r.get("task_id")
            if tid:
                st.session_state["kb_compile_task_id"] = tid
            st.success(f"В очереди: task_id={tid or r}")
    if c2.button("Запустить lint_kb (Celery)"):
        r = api_post("/kb/lint")
        if r:
            tid = r.get("task_id")
            if tid:
                st.session_state["kb_lint_task_id"] = tid
            st.success(f"В очереди: task_id={tid or r}")

    st.subheader("Статус фоновых задач (Celery)")
    st.caption("Read-only GET /tasks/{task_id} — state и ready, без тела результата.")
    last_c = st.session_state.get("kb_compile_task_id")
    last_l = st.session_state.get("kb_lint_task_id")
    st.caption(f"Последние из UI: compile=`{last_c or '—'}` lint=`{last_l or '—'}`")
    kb_tid = st.text_input("task_id для опроса", key="kb_poll_task_id", placeholder="UUID из ответа /kb/compile или /kb/lint")
    if st.button("Опросить статус задачи"):
        tid = (kb_tid or "").strip() or last_c or last_l or ""
        if tid:
            stat = api_get(f"/tasks/{tid}")
            if stat:
                st.write(f"**state**={stat.get('state')} **ready**={stat.get('ready')}")
        else:
            st.warning("Укажите task_id или сначала запустите compile/lint.")

    st.subheader("Артефакты")
    f1, f2, f3 = st.columns(3)
    atype = f1.text_input("Тип артефакта (опц.)", "", placeholder="source_digest")
    qsearch = f2.text_input("Поиск (title/summary/slug)", "")
    psize = f3.number_input("page_size", min_value=5, max_value=200, value=50)
    params: dict = {"page": 1, "page_size": int(psize)}
    if atype.strip():
        params["artifact_type"] = atype.strip()
    if qsearch.strip():
        params["search"] = qsearch.strip()
    arts = api_get("/kb/artifacts", params)
    if arts and arts.get("items"):
        df = pd.DataFrame(arts["items"])
        st.caption(f"Всего: {arts.get('total', 0)}")
        show_cols = [c for c in ("id", "artifact_type", "canonical_slug", "title", "status") if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True)
    elif arts:
        st.info("Артефактов нет — сначала normalize + compile для версий документов.")

    st.subheader("Сущности entity_registry (список)")
    e1, e2, e3 = st.columns(3)
    et_filter = e1.text_input("Тип сущности", "", placeholder="molecule", key="kb_ent_type")
    ent_search = e2.text_input("Поиск по имени", "", key="kb_ent_search")
    ent_psize = e3.number_input("page_size entities", min_value=5, max_value=200, value=30, key="kb_ent_psize")
    ent_params: dict = {"page": 1, "page_size": int(ent_psize)}
    if et_filter.strip():
        ent_params["entity_type"] = et_filter.strip()
    if ent_search.strip():
        ent_params["search"] = ent_search.strip()
    ent_list = api_get("/kb/entities", ent_params)
    if ent_list and ent_list.get("items"):
        edf = pd.DataFrame(ent_list["items"])
        st.caption(f"Сущностей: {ent_list.get('total', 0)}")
        ecs = [c for c in ("id", "entity_type", "canonical_name", "status") if c in edf.columns]
        st.dataframe(edf[ecs], use_container_width=True)
    elif ent_list:
        st.info("Нет сущностей — после extract с МНН появятся molecule; compile создаёт document.")

    st.subheader("Деталь артефакта")
    aid = st.number_input("artifact_id", min_value=1, step=1, value=1, key="kb_artifact_id")
    if st.button("Загрузить артефакт", key="kb_load_art"):
        det = api_get(f"/kb/artifacts/{int(aid)}")
        if det:
            st.json({k: det.get(k) for k in ("id", "artifact_type", "canonical_slug", "title", "status") if k in det})
            if det.get("content_md"):
                st.markdown("---")
                st.text_area("content_md", det["content_md"], height=320, disabled=True)

    st.subheader("Группы конфликтов")
    cfs = api_get("/kb/conflicts")
    if cfs is not None:
        if cfs:
            st.dataframe(pd.DataFrame([{"conflict_group_id": x.get("conflict_group_id"), "claims": len(x.get("claim_ids", []))} for x in cfs]), use_container_width=True)
        else:
            st.info("Нет claim с conflict_group_id")

    st.subheader("Claims (GET /kb/claims)")
    q1, q2 = st.columns(2)
    claim_artifact = q1.number_input("artifact_id (0 = без фильтра)", min_value=0, value=0, key="kb_claims_artifact")
    claim_psize = q2.number_input("page_size claims", min_value=5, max_value=200, value=50, key="kb_claims_psize")
    cparams: dict = {"page": 1, "page_size": int(claim_psize)}
    if claim_artifact > 0:
        cparams["artifact_id"] = int(claim_artifact)
    clm = api_get("/kb/claims", cparams)
    if clm and clm.get("items"):
        cdf = pd.DataFrame(clm["items"])
        st.caption(f"Всего claims: {clm.get('total', 0)}")
        ccols = [c for c in ("id", "artifact_id", "claim_type", "claim_text", "review_status", "conflict_group_id") if c in cdf.columns]
        st.dataframe(cdf[ccols] if ccols else cdf, use_container_width=True)
    elif clm:
        st.info("Claims не найдены для заданных параметров.")

    st.subheader("Деталь сущности entity_registry")
    eid = st.number_input("entity_id", min_value=1, step=1, value=1, key="kb_entity_id")
    if st.button("Загрузить сущность", key="kb_load_ent"):
        ent = api_get(f"/kb/entities/{int(eid)}")
        if ent:
            st.json(ent)


# --- Page: Matrix ---

def page_matrix():
    st.header("Substitution Matrix")

    st.subheader("Пересчёт матрицы (Celery)")
    st.caption("POST /matrix/rebuild — цепочка score_pairs → build_matrix (очередь score). Нужен model_version_id.")
    mr1, mr2, mr3 = st.columns(3)
    mvid = mr1.number_input("model_version_id", min_value=1, step=1, value=1, key="matrix_rebuild_mvid")
    mscope = mr2.selectbox("scope_type", ["global", "disease"], key="matrix_rebuild_scope")
    if mr3.button("Запустить /matrix/rebuild"):
        rb = api_post("/matrix/rebuild", {"model_version_id": int(mvid), "scope_type": mscope})
        if rb:
            rtid = rb.get("task_id")
            if rtid:
                st.session_state["matrix_rebuild_task_id"] = rtid
            st.success(f"В очереди: task_id={rtid or rb}")
    last_mtx = st.session_state.get("matrix_rebuild_task_id")
    if last_mtx:
        st.caption(f"Последний rebuild task_id: `{last_mtx}` — опрос: вкладка Knowledge base → статус задач или GET /tasks/{{id}}")
    st.markdown("---")

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
        "Knowledge base": page_knowledge_base,
        "Matrix": page_matrix,
        "Reviews": page_reviews,
        "Scoring Models": page_scoring_models,
    }

    page = st.sidebar.radio("Navigation", list(pages.keys()))
    pages[page]()


if __name__ == "__main__":
    main()

"""CR Intelligence Platform — Streamlit Admin UI."""

from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd
import streamlit as st

try:
    from app.ui.ui_i18n import (
        LANGUAGE_OPTIONS,
        init_language_state,
        install_streamlit_i18n,
        language_label,
        persist_language,
        tr,
    )
except ModuleNotFoundError:
    from ui_i18n import (  # type: ignore[no-redef]
        LANGUAGE_OPTIONS,
        init_language_state,
        install_streamlit_i18n,
        language_label,
        persist_language,
        tr,
    )

API_BASE = "http://app:8000"


def append_recent_task(
    recent_tasks: list[dict],
    *,
    task_id: str,
    label: str,
    origin: str,
    max_items: int = 10,
) -> list[dict]:
    filtered_tasks = [item for item in recent_tasks if item.get("task_id") != task_id]
    return [
        {
            "task_id": task_id,
            "label": label,
            "origin": origin,
            "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
        *filtered_tasks,
    ][:max_items]


def remember_task(task_id: str | None, *, label: str, origin: str) -> None:
    if not task_id:
        return
    recent_tasks = st.session_state.get("recent_tasks") or []
    st.session_state["recent_tasks"] = append_recent_task(
        recent_tasks,
        task_id=task_id,
        label=label,
        origin=origin,
    )


def format_pipeline_run_label(run: dict) -> str:
    return (
        f"#{run.get('id')} | {run.get('stage')} | "
        f"{run.get('run_type')} | {run.get('status')}"
    )


def format_pipeline_stage_option(stage: str) -> str:
    return tr("All") if not stage else tr(stage)


def build_matrix_query_params(
    *,
    page_size: int,
    scope_type: str,
    scope_id: str,
    model_version_id: int,
    molecule_from_id: int,
) -> dict:
    params = {"page": 1, "page_size": page_size}
    if scope_type:
        params["scope_type"] = scope_type
    if scope_id.strip():
        params["scope_id"] = scope_id.strip()
    if model_version_id > 0:
        params["model_version_id"] = model_version_id
    if molecule_from_id > 0:
        params["molecule_from_id"] = molecule_from_id
    return params


def build_matrix_cell_detail_params(
    *,
    molecule_from_id: int,
    molecule_to_id: int,
    scope_type: str,
    model_version_id: int,
) -> dict:
    params = {
        "molecule_from_id": molecule_from_id,
        "molecule_to_id": molecule_to_id,
        "scope_type": scope_type,
    }
    if model_version_id > 0:
        params["model_version_id"] = model_version_id
    return params


def build_bulk_approve_evidence_ids(manual_ids: str, selected_ids: list[int]) -> list[int]:
    evidence_ids: list[int] = []
    seen_ids: set[int] = set()
    for raw_value in manual_ids.split(","):
        stripped_value = raw_value.strip()
        if not stripped_value:
            continue
        parsed_id = int(stripped_value)
        if parsed_id in seen_ids:
            continue
        seen_ids.add(parsed_id)
        evidence_ids.append(parsed_id)
    for selected_id in selected_ids:
        if selected_id in seen_ids:
            continue
        seen_ids.add(selected_id)
        evidence_ids.append(selected_id)
    return evidence_ids


def resolve_review_target_id(manual_target_id: int, queued_target_id: int | None) -> int:
    return queued_target_id or manual_target_id


def resolve_history_target_id(manual_target_id: int, queued_target_id: int | None) -> int:
    return queued_target_id or manual_target_id


def resolve_document_id(manual_document_id: int, selected_document_id: int | None) -> int:
    return selected_document_id or manual_document_id


def resolve_output_id(manual_output_id: int, selected_output_id: int | None) -> int:
    return selected_output_id or manual_output_id


def resolve_artifact_id(manual_artifact_id: int, selected_artifact_id: int | None) -> int:
    return selected_artifact_id or manual_artifact_id


def resolve_entity_id(manual_entity_id: int, selected_entity_id: int | None) -> int:
    return selected_entity_id or manual_entity_id


def resolve_task_id(manual_task_id: str, selected_task_id: str | None) -> str:
    return selected_task_id or manual_task_id.strip()


def filter_recent_tasks(recent_tasks: list[dict[str, Any]], origin_filter: str) -> list[dict[str, Any]]:
    if not origin_filter:
        return recent_tasks
    return [item for item in recent_tasks if item.get("origin") == origin_filter]


def search_recent_tasks(recent_tasks: list[dict[str, Any]], search_query: str) -> list[dict[str, Any]]:
    stripped_query = search_query.strip().lower()
    if not stripped_query:
        return recent_tasks
    return [item for item in recent_tasks if stripped_query in str(item.get("label", "")).lower()]


def sort_recent_tasks(recent_tasks: list[dict[str, Any]], sort_order: str) -> list[dict[str, Any]]:
    return sorted(
        recent_tasks,
        key=lambda item: str(item.get("queued_at", "")),
        reverse=sort_order != "oldest",
    )


def filter_document_items(document_items: list[dict[str, Any]], status_filter: str) -> list[dict[str, Any]]:
    if not status_filter:
        return document_items
    return [item for item in document_items if str(item.get("status", "")) == status_filter]


def sort_document_items(document_items: list[dict[str, Any]], sort_order: str) -> list[dict[str, Any]]:
    return sorted(
        document_items,
        key=lambda item: int(item.get("id") or 0),
        reverse=sort_order != "oldest",
    )


def filter_document_artifacts(artifacts: list[dict[str, Any]], artifact_type_filter: str) -> list[dict[str, Any]]:
    if not artifact_type_filter:
        return artifacts
    return [artifact for artifact in artifacts if str(artifact.get("artifact_type", "")) == artifact_type_filter]


def filter_document_sections(sections: list[dict[str, Any]], section_search: str) -> list[dict[str, Any]]:
    stripped_query = section_search.strip().lower()
    if not stripped_query:
        return sections
    filtered_sections: list[dict[str, Any]] = []
    for section in sections:
        title = str(section.get("section_title", "")).lower()
        fragments = section.get("fragments", [])
        if stripped_query in title:
            filtered_sections.append(section)
            continue
        matched_fragments = [
            fragment
            for fragment in fragments
            if stripped_query in str(fragment.get("fragment_text", "")).lower()
        ]
        if matched_fragments:
            filtered_sections.append({**section, "fragments": matched_fragments})
    return filtered_sections


def filter_pipeline_runs(run_items: list[dict[str, Any]], status_filter: str) -> list[dict[str, Any]]:
    if not status_filter:
        return run_items
    return [item for item in run_items if str(item.get("status", "")) == status_filter]


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
    st.markdown(f"**{detail.get('title', tr('KB Artifact'))}**")
    source_links = detail.get("source_links") or []
    meta1, meta2, meta3, meta4, meta5, meta6 = st.columns(6)
    meta1.metric(tr("Artifact ID"), detail.get("id"))
    meta2.metric(tr("Type"), tr(detail.get("artifact_type") or "n/a"))
    meta3.metric(tr("Status"), tr(detail.get("status") or "n/a"))
    meta4.metric(tr("Review"), tr(detail.get("review_status") or "n/a"))
    meta5.metric(tr("Claims"), len(detail.get("claims") or []))
    meta6.metric(tr("Sources"), len(source_links))

    if detail.get("generator_version"):
        st.caption(tr("generator={value}", value=detail.get("generator_version")))

    if detail.get("summary"):
        st.caption(detail.get("summary"))

    if detail.get("manifest_json"):
        with st.expander("Manifest", expanded=False):
            st.json(detail.get("manifest_json"))

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
    st.markdown(f"**{detail.get('title', tr('Output'))}**")
    meta1, meta2, meta3, meta4, meta5 = st.columns(5)
    meta1.metric(tr("Output ID"), detail.get("id"))
    meta2.metric(tr("Type"), tr(detail.get("output_type") or "n/a"))
    meta3.metric(tr("File-Back"), tr(detail.get("file_back_status") or "n/a"))
    meta4.metric(tr("Review"), tr(detail.get("review_status") or "n/a"))
    meta5.metric(tr("Artifact"), tr(str(detail.get("artifact_id"))) if detail.get("artifact_id") else tr("none"))

    if detail.get("released_at") or detail.get("generator_version"):
        st.caption(
            tr(
                "released_at={released_at} | generator={generator}",
                released_at=detail.get("released_at") or tr("n/a"),
                generator=detail.get("generator_version") or tr("n/a"),
            )
        )

    if detail.get("scope_json"):
        with st.expander("Scope", expanded=False):
            st.json(detail.get("scope_json"))

    if detail.get("file_pointer"):
        st.code(detail.get("file_pointer"), language="text")

    with st.expander("Raw Payload", expanded=False):
        st.json(detail)


def render_entity_detail(detail: dict) -> None:
    st.caption(tr("Entity #{id}", id=detail.get("id")))
    meta1, meta2, meta3 = st.columns(3)
    meta1.metric(tr("Type"), tr(detail.get("entity_type") or "n/a"))
    meta2.metric(tr("Status"), tr(detail.get("status") or "n/a"))
    meta3.metric(tr("Aliases"), len(detail.get("aliases_json") or {}))
    st.subheader(detail.get("canonical_name") or tr("Untitled entity"))

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
        st.error(tr("API error: {error}", error=e))
        return None


def api_post(path: str, json: dict | None = None) -> dict | None:
    """Make POST request to backend API."""
    try:
        resp = httpx.post(f"{API_BASE}{path}", json=json, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as e:
        st.error(tr("API error: {error}", error=e))
        return None


# --- Page: Dashboard ---

def page_dashboard():
    st.header("Dashboard")

    col1, col2, col3, col4, col5 = st.columns(5)

    # Documents stats
    docs = api_get("/documents", {"page_size": 1})
    if docs:
        col1.metric(tr("Documents"), docs.get("total", 0))

    # Matrix stats
    matrix = api_get("/matrix", {"page_size": 1})
    if matrix:
        col2.metric(tr("Matrix Cells"), matrix.get("total", 0))

    # Pipeline runs
    runs = api_get("/runs", {"page_size": 1})
    if runs:
        col3.metric(tr("Pipeline Runs"), runs.get("total", 0))

    # Output releases
    outputs = api_get("/outputs", {"page_size": 1})
    if outputs:
        col4.metric(tr("Outputs"), outputs.get("total", 0))

    # Knowledge artifacts
    kb_artifacts = api_get("/kb/artifacts", {"page_size": 1})
    if kb_artifacts:
        col5.metric(tr("KB Artifacts"), kb_artifacts.get("total", 0))

    # Health check
    st.subheader("System Health")
    health = api_get("/health")
    if health:
        status = health.get("status", "unknown")
        if status == "ok":
            st.success("All systems operational")
        else:
            st.warning(tr("Status: {status}", status=status))
            if health.get("db_error"):
                st.error(tr("DB: {error}", error=health["db_error"]))

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
                tr(
                    "Active scoring model: #{id} {label}",
                    id=active_model.get("id"),
                    label=active_model.get("version_label"),
                )
            )
        else:
            st.warning("No active scoring model")

        if isinstance(kb_master, dict):
            st.success(
                tr(
                    "KB master index available: artifact #{id} ({fmt})",
                    id=kb_master.get("artifact_id"),
                    fmt=kb_master.get("format"),
                )
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
    st.header(tr("Document Registry"))

    col1, col2 = st.columns(2)
    search = col1.text_input(tr("Search"), "")
    specialty = col2.text_input(tr("Specialty filter"), "")

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

    document_status_options = [""] + sorted(
        {str(item.get("status", "")) for item in items if item.get("status")}
    )
    selected_status = st.selectbox(
        tr("Document Status Filter"),
        document_status_options,
        format_func=lambda value: tr("All Statuses") if not value else tr(value),
        key="document_status_filter",
    )
    document_sort_order = st.selectbox(
        tr("Document Sort Order"),
        ["newest", "oldest"],
        format_func=lambda value: tr("Newest First") if value == "newest" else tr("Oldest First"),
        key="document_sort_order",
    )
    filtered_items = sort_document_items(filter_document_items(items, selected_status), document_sort_order)
    if not filtered_items:
        st.info("No documents found")
        return

    df = pd.DataFrame(filtered_items)
    display_cols = ["id", "title", "specialty", "status", "external_id"]
    display_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[display_cols], width="stretch")

    # Document detail
    st.subheader(tr("Document Detail"))
    current_document_options = {
        item["id"]: f"#{item['id']} | {item.get('title')}"
        for item in filtered_items
        if item.get("id") is not None
    }
    selected_document_id = st.selectbox(
        tr("Current Document"),
        [None, *list(current_document_options)],
        format_func=lambda value: tr("Manual Document ID") if value is None else current_document_options[value],
    )
    doc_id = st.number_input(tr("Document ID"), min_value=1, step=1)
    if st.button(tr("Load Document")):
        resolved_doc_id = resolve_document_id(doc_id, selected_document_id)
        detail = api_get(f"/documents/{resolved_doc_id}")
        if detail:
            st.json(detail)

        artifacts = api_get(f"/documents/{resolved_doc_id}/artifacts")
        st.subheader("Raw Source Artifacts")
        if isinstance(artifacts, dict) and artifacts.get("artifacts"):
            artifact_items = artifacts.get("artifacts", [])
            artifact_type_options = [""] + sorted(
                {str(artifact.get("artifact_type", "")) for artifact in artifact_items if artifact.get("artifact_type")}
            )
            selected_artifact_type = st.selectbox(
                tr("Artifact Type Filter"),
                artifact_type_options,
                format_func=lambda value: tr("All") if not value else tr(value),
                key=f"document_artifact_type_filter_{resolved_doc_id}",
            )
            for artifact in filter_document_artifacts(artifact_items, selected_artifact_type):
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.write(
                    f"#{artifact.get('id')} {artifact.get('artifact_type')} "
                    f"({artifact.get('content_type') or 'application/octet-stream'})"
                )
                col2.link_button("Download", f"{API_BASE}{artifact.get('download_url')}")
                col3.link_button("Preview", f"{API_BASE}{artifact.get('preview_url')}")
        else:
            st.info("No valid raw artifacts available for current version")

        content = api_get(f"/documents/{resolved_doc_id}/content")
        if content:
            section_search = st.text_input(
                tr("Section Search"),
                key=f"document_section_search_{resolved_doc_id}",
            )
            sections = filter_document_sections(content.get("sections", []), section_search)
            for sec in sections:
                with st.expander(sec.get("section_title", "Section")):
                    fragments = sec.get("fragments", [])
                    for frag in fragments:
                        st.text(frag.get("fragment_text", "")[:500])


# --- Page: Pipeline ---

def page_pipeline():
    st.header(tr("Pipeline Management"))

    col1, col2 = st.columns(2)
    if col1.button(tr("Run Full Sync"), type="primary"):
        result = api_post("/sync/full")
        if result:
            remember_task(result.get("task_id"), label="sync_full", origin="pipeline")
            st.success(tr("Pipeline run started: ID {run_id}", run_id=result.get("run_id")))

    if col2.button(tr("Run Incremental Sync")):
        result = api_post("/sync/incremental")
        if result:
            remember_task(result.get("task_id"), label="sync_incremental", origin="pipeline")
            st.success(tr("Pipeline run started: ID {run_id}", run_id=result.get("run_id")))

    stage_filter = st.selectbox(
        tr("Stage Filter"),
        ["", "probe", "discovery", "fetch", "normalize", "extract"],
        format_func=format_pipeline_stage_option,
        key="pipeline_stage_filter",
    )
    pipeline_status_filter = st.selectbox(
        tr("Pipeline Status Filter"),
        ["", "queued", "running", "completed", "failed"],
        format_func=lambda value: tr("All Statuses") if not value else tr(value),
        key="pipeline_status_filter",
    )

    # Recent runs
    st.subheader(tr("Recent Pipeline Runs"))
    run_params = {"page_size": 20}
    if stage_filter:
        run_params["stage"] = stage_filter
    runs = api_get("/runs", run_params)
    if runs:
        items = filter_pipeline_runs(runs.get("items", []), pipeline_status_filter)
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, width="stretch")

            st.subheader(tr("Run Detail"))
            recent_run_map = {item["id"]: item for item in items if item.get("id") is not None}
            selected_run_id = st.selectbox(
                tr("Recent Run"),
                list(recent_run_map),
                format_func=lambda run_id: format_pipeline_run_label(recent_run_map[run_id]),
                key="pipeline_recent_run_id",
            )
            if st.button(tr("Load Selected Run")):
                detail = api_get(f"/runs/{selected_run_id}")
                if detail:
                    st.json(detail)
        else:
            st.info("No pipeline runs yet")


# --- Page: Matrix ---

def page_matrix():
    st.header(tr("Substitution Matrix"))

    col1, col2, col3, col4, col5 = st.columns(5)
    scope_type = col1.selectbox(tr("Scope"), ["global", "disease"], format_func=tr)
    scope_id = col2.text_input(tr("Scope ID Filter"))
    model_version_id = col3.number_input(
        tr("Model Version ID Filter"),
        min_value=0,
        step=1,
        help=tr("0 means no model filter"),
    )
    molecule_from_id = col4.number_input(
        tr("Molecule From Filter"),
        min_value=0,
        step=1,
        help=tr("0 means no molecule filter"),
    )
    page_size = col5.number_input(tr("Page size"), min_value=10, max_value=500, value=50)

    params = build_matrix_query_params(
        page_size=page_size,
        scope_type=scope_type,
        scope_id=scope_id,
        model_version_id=model_version_id,
        molecule_from_id=molecule_from_id,
    )

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
    st.subheader(tr("Export Matrix"))
    fmt = st.selectbox(tr("Format"), ["csv", "jsonl"])
    if st.button(tr("Download")):
        st.info(tr("Use API endpoint: GET /matrix/export?format={fmt}", fmt=fmt))

    # Cell detail
    st.subheader(tr("Cell Detail"))
    col1, col2, col3, col4 = st.columns(4)
    mol_from = col1.number_input(tr("Molecule From ID"), min_value=1, step=1)
    mol_to = col2.number_input(tr("Molecule To ID"), min_value=1, step=1)
    cell_scope_type = col3.selectbox(tr("Cell Scope"), ["global", "disease"], format_func=tr)
    detail_model_version_id = col4.number_input(
        tr("Cell Model Version ID"),
        min_value=0,
        step=1,
        help=tr("0 means latest available model"),
    )
    if st.button("Load Cell Detail"):
        detail = api_get(
            "/matrix/cell",
            build_matrix_cell_detail_params(
                molecule_from_id=mol_from,
                molecule_to_id=mol_to,
                scope_type=cell_scope_type,
                model_version_id=detail_model_version_id,
            ),
        )
        if detail:
            st.json(detail)


# --- Page: Reviews ---

def page_reviews():
    st.header(tr("Reviewer Queue"))

    stats = api_get("/review/stats")
    if isinstance(stats, dict):
        counts = stats.get("counts", {})
        col1, col2, col3 = st.columns(3)
        col1.metric(tr("Auto"), counts.get("auto", 0))
        col2.metric(tr("Approved"), counts.get("approved", 0))
        col3.metric(tr("Rejected"), counts.get("rejected", 0))

    st.subheader(tr("Queue"))
    queue_document_version_id = st.number_input(
        tr("Queue Document Version ID"),
        min_value=0,
        step=1,
        help=tr("0 means no document filter"),
    )
    queue_params = {"status": "auto", "page_size": 50}
    if queue_document_version_id > 0:
        queue_params["document_version_id"] = queue_document_version_id
    queue = api_get("/review/queue", queue_params)
    if isinstance(queue, dict):
        items = queue.get("items", [])
        if items:
            queue_rows = []
            for item in items:
                queue_rows.append(
                    {
                        "id": item.get("id"),
                        "context_id": item.get("context_id"),
                        "from": item.get("molecule_from_id"),
                        "to": item.get("molecule_to_id"),
                        "relation": item.get("relation_type"),
                        "score": item.get("final_fragment_score"),
                        "review_status": item.get("review_status"),
                    }
                )
            st.dataframe(pd.DataFrame(queue_rows), width="stretch", hide_index=True)
        else:
            st.info("No evidence awaiting review")
    else:
        items = []

    # Review history
    st.subheader(tr("Recent Review Actions"))
    history_col1, history_col2 = st.columns(2)
    history_target_type = history_col1.selectbox(
        tr("History Target Type"),
        ["", "pair_evidence"],
        index=0,
    )
    queued_history_options = {
        item["id"]: f"#{item['id']} | {item.get('relation_type')} | {item.get('final_fragment_score')}"
        for item in items
        if item.get("id") is not None
    }
    selected_history_target_id = history_col1.selectbox(
        tr("History Target From Queue"),
        [None, *list(queued_history_options)],
        format_func=lambda value: tr("Manual History Target") if value is None else queued_history_options[value],
    )
    history_target_id = history_col2.number_input(
        tr("History Target ID"),
        min_value=0,
        step=1,
        help=tr("0 means no target filter"),
    )
    history_params = {"page_size": 50}
    if history_target_type:
        history_params["target_type"] = history_target_type
    resolved_history_target_id = resolve_history_target_id(history_target_id, selected_history_target_id)
    if resolved_history_target_id > 0:
        history_params["target_id"] = resolved_history_target_id
    reviews = api_get("/review/history", history_params)
    if isinstance(reviews, dict):
        items = reviews.get("items", [])
        if items:
            history_rows = []
            for item in items:
                history_rows.append(
                    {
                        "id": item.get("id"),
                        "target_type": item.get("target_type"),
                        "target_id": item.get("target_id"),
                        "action": item.get("action"),
                        "author": item.get("author"),
                        "reason": item.get("reason"),
                        "created_at": item.get("created_at"),
                    }
                )
            st.dataframe(pd.DataFrame(history_rows), width="stretch", hide_index=True)
        else:
            st.info("No review actions yet")

    st.subheader(tr("Bulk Approve"))
    with st.form("bulk_review_form"):
        bulk_ids = st.text_input(tr("Evidence IDs (comma-separated)"))
        queued_evidence_options = {
            item["id"]: f"#{item['id']} | {item.get('relation_type')} | {item.get('final_fragment_score')}"
            for item in items
            if item.get("id") is not None
        }
        selected_evidence_ids = st.multiselect(
            tr("Queued Evidence IDs"),
            list(queued_evidence_options),
            format_func=lambda evidence_id: queued_evidence_options[evidence_id],
            help=tr("Optional quick-pick from current review queue"),
        )
        bulk_author = st.text_input(tr("Bulk Approve Author"))
        st.caption(tr("Use the filtered queue above to identify evidence IDs for bulk approval."))
        if st.form_submit_button(tr("Bulk Approve")):
            evidence_ids = build_bulk_approve_evidence_ids(bulk_ids, selected_evidence_ids)
            if not evidence_ids:
                st.warning("Enter at least one evidence ID")
            else:
                result = api_post(
                    "/review/bulk-approve",
                    {"evidence_ids": evidence_ids, "author": bulk_author},
                )
                if result:
                    st.success(
                        tr("Approved {count} evidence items", count=result.get("approved_count", 0))
                    )

    # Submit review
    st.subheader(tr("Submit Review"))
    with st.form("review_form"):
        target_type = st.selectbox(tr("Target Type"), ["pair_evidence"])
        queued_target_options = {
            item["id"]: f"#{item['id']} | {item.get('relation_type')} | {item.get('final_fragment_score')}"
            for item in items
            if item.get("id") is not None
        }
        selected_queue_target_id = st.selectbox(
            tr("Queued Evidence Target"),
            [None, *list(queued_target_options)],
            format_func=lambda value: tr("Manual Target ID") if value is None else queued_target_options[value],
        )
        target_id = st.number_input(tr("Target ID"), min_value=1, step=1)
        action = st.selectbox(tr("Action"), ["approve", "reject", "override"])
        reason = st.text_area(tr("Reason"))
        author = st.text_input(tr("Author"))
        override_score = None
        if action == "override":
            override_score = st.number_input(tr("Override Score"), min_value=0.0, max_value=1.0, step=0.01)

        if st.form_submit_button(tr("Submit")):
            payload = {
                "target_type": target_type,
                "target_id": resolve_review_target_id(target_id, selected_queue_target_id),
                "action": action,
                "reason": reason,
                "author": author,
            }
            if action == "override":
                payload["new_value_json"] = {"final_fragment_score": override_score}
            result = api_post("/review", payload)
            if result:
                st.success(tr("Review submitted"))


# --- Page: Scoring Models ---

def page_scoring_models():
    st.header(tr("Scoring Models"))

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
                tr(
                    "Active scoring model: #{id} {label}",
                    id=active_model.get("id"),
                    label=active_model.get("version_label"),
                )
            )

        model_options = {
            f"#{model['id']} {model['version_label']}": model["id"] for model in models
        }
        selected_label = st.selectbox(tr("Selected Model"), list(model_options.keys()))
        selected_model_id = model_options[selected_label]

        summary = api_get(f"/matrix/models/{selected_model_id}/summary")
        if isinstance(summary, dict):
            readiness = summary.get("readiness", {})
            col1, col2, col3 = st.columns(3)
            col1.metric(tr("Ready"), tr("yes") if readiness.get("ready") else tr("no"))
            col2.metric(tr("Cells"), readiness.get("cell_count", 0))
            col3.metric(tr("Pair Scores"), readiness.get("pcs_count", 0))

        st.subheader(tr("Model Actions"))
        with st.form("model_refresh_form"):
            refresh_scope_type = st.selectbox(tr("Refresh Scope Type"), ["global"], key="refresh_scope_type")
            refresh_scope_id = st.text_input(tr("Refresh Scope ID"), value="", key="refresh_scope_id")
            if st.form_submit_button(tr("Refresh Model")):
                payload = {
                    "scope_type": refresh_scope_type,
                    "scope_id": refresh_scope_id or None,
                }
                result = api_post(f"/matrix/models/{selected_model_id}/refresh", payload)
                if result:
                    st.success(
                        tr(
                            "Refreshed: {pair_scores} pair scores, {matrix_cells} matrix cells",
                            pair_scores=result.get("pair_context_scores", 0),
                            matrix_cells=result.get("matrix_cells", 0),
                        )
                    )

        with st.form("model_activate_form"):
            activate_author = st.text_input(tr("Activation Author"), key="activate_author")
            activate_force = st.checkbox(tr("Force Activate"), value=False)
            if st.form_submit_button(tr("Activate Model")):
                result = api_post(
                    f"/matrix/models/{selected_model_id}/activate",
                    {"author": activate_author, "force": activate_force},
                )
                if result:
                    st.success(tr("Activated model {label}", label=result.get("version_label")))

        st.subheader(tr("Model Diff"))
        diff_options = {
            f"#{model['id']} {model['version_label']}": model["id"] for model in models
        }
        diff_left = st.selectbox(tr("Old Version"), list(diff_options.keys()), key="diff_left")
        diff_right = st.selectbox(tr("New Version"), list(diff_options.keys()), key="diff_right")
        if st.button(tr("Load Diff")):
            diff = api_get(
                "/matrix/models/diff",
                {
                    "old_version_id": diff_options[diff_left],
                    "new_version_id": diff_options[diff_right],
                },
            )
            if isinstance(diff, dict):
                diff_col1, diff_col2, diff_col3 = st.columns(3)
                diff_col1.metric(tr("Added"), diff.get("added", 0))
                diff_col2.metric(tr("Removed"), diff.get("removed", 0))
                diff_col3.metric(tr("Changed"), diff.get("changed", 0))

                details = diff.get("details", {})
                for section in ("added", "changed", "removed"):
                    rows = details.get(section) or []
                    if rows:
                        st.markdown(f"**{tr(section.title())}**")
                        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info(tr("No scoring models defined"))

    # Create new model
    st.subheader(tr("Create Scoring Model Version"))
    with st.form("model_form"):
        label = st.text_input(tr("Version Label"), "v1.0")
        weights_str = st.text_area(
            tr("Weights JSON"),
            '{"role": 0.2, "text": 0.25, "population": 0.15, "parity": 0.15, "practical": 0.1, "penalty": 0.15}',
        )

        if st.form_submit_button(tr("Create")):
            import json
            try:
                weights = json.loads(weights_str)
            except json.JSONDecodeError:
                st.error(tr("Invalid JSON"))
                return

            result = api_post("/matrix/models", {"version_label": label, "weights_json": weights})
            if result:
                st.success(tr("Model created: ID {id}", id=result.get("id")))


# --- Page: Outputs ---

def page_outputs():
    st.header(tr("Outputs"))

    out_col1, out_col2, out_col3, out_col4, out_col5 = st.columns(5)
    output_type_filter = out_col1.selectbox(tr("Output Type Filter"), ["", "memo"], index=0)
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
    generator_version_filter = out_col4.text_input(tr("Generator Version Filter"))
    output_artifact_id = out_col5.number_input(
        "Artifact ID Filter",
        min_value=0,
        step=1,
        help="0 means no artifact filter",
    )
    output_search = st.text_input(tr("Output Search"))
    released_only = st.checkbox(tr("Released Outputs Only"))
    has_file_pointer = st.checkbox(tr("Outputs With Files Only"))
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
    if has_file_pointer:
        params["has_file_pointer"] = True
    if output_artifact_id > 0:
        params["artifact_id"] = output_artifact_id
    if output_search:
        params["search"] = output_search

    outputs = api_get("/outputs", params)
    if isinstance(outputs, dict):
        items = outputs.get("items", [])
        if items:
            output_rows = []
            for item in items:
                output_rows.append(
                    {
                        "id": item.get("id"),
                        "type": item.get("output_type"),
                        "title": item.get("title"),
                        "artifact_id": item.get("artifact_id"),
                        "review_status": item.get("review_status"),
                        "file_back_status": item.get("file_back_status"),
                        "generator_version": item.get("generator_version"),
                        "released_at": item.get("released_at"),
                    }
                )
            st.dataframe(pd.DataFrame(output_rows), width="stretch", hide_index=True)
        else:
            st.info(tr("No outputs available"))

    st.subheader(tr("Output Detail"))
    current_output_options = {
        item["id"]: f"#{item['id']} | {item.get('output_type')} | {item.get('title') or 'untitled'}"
        for item in items
        if item.get("id") is not None
    }
    selected_output_id = st.selectbox(
        tr("Current Output"),
        [None, *list(current_output_options)],
        format_func=lambda value: tr("Manual Output ID") if value is None else current_output_options[value],
        key="current_output_id",
    )
    detail_output_id = st.number_input(tr("Detail Output ID"), min_value=1, step=1, key="detail_output_id")
    if st.button(tr("Load Output Detail")):
        resolved_output_id = resolve_output_id(detail_output_id, selected_output_id)
        detail = api_get(f"/outputs/{resolved_output_id}")
        if detail:
            render_output_detail(detail)
            artifact_id = detail.get("artifact_id")
            if artifact_id:
                st.success(tr("Linked KB artifact: #{id}", id=artifact_id))
                if st.button(tr("Load Linked Artifact"), key=f"load_output_artifact_{artifact_id}"):
                    artifact = api_get(f"/kb/artifacts/{artifact_id}")
                    if artifact:
                        render_kb_artifact_detail(artifact)

    st.subheader(tr("Generate Output"))
    with st.form("output_generate_form"):
        output_type = st.selectbox(tr("Output Type"), ["memo"])
        title = st.text_input(tr("Title"))
        if st.form_submit_button(tr("Queue Generation")):
            result = api_post(
                "/outputs/generate",
                {"output_type": output_type, "title": title or None, "scope_json": None},
            )
            if result:
                remember_task(result.get("task_id"), label="output_generate", origin="outputs")
                st.success(tr("Generation queued: {task_id}", task_id=result.get("task_id")))

    st.subheader(tr("File Back Output"))
    with st.form("output_file_back_form"):
        file_back_output_options = {
            item["id"]: f"#{item['id']} | {item.get('output_type')} | {item.get('title') or 'untitled'}"
            for item in items
            if item.get("id") is not None
        }
        selected_file_back_output_id = st.selectbox(
            tr("Current File-Back Output"),
            [None, *list(file_back_output_options)],
            format_func=lambda value: tr("Manual File-Back Output ID") if value is None else file_back_output_options[value],
            key="current_file_back_output_id",
        )
        output_id = st.number_input(tr("Output ID"), min_value=1, step=1)
        file_back_status = st.selectbox(tr("File Back Status"), ["accepted", "rejected", "needs_review"])
        if st.form_submit_button(tr("Queue File Back")):
            result = api_post(
                f"/outputs/file-back/{resolve_output_id(output_id, selected_file_back_output_id)}",
                {"file_back_status": file_back_status},
            )
            if result:
                remember_task(result.get("task_id"), label="output_file_back", origin="outputs")
                st.success(tr("File-back queued: {task_id}", task_id=result.get("task_id")))


# --- Page: Knowledge Base ---

def page_kb():
    st.header(tr("Knowledge Base"))

    col1, col2 = st.columns(2)
    if col1.button(tr("Compile KB")):
        result = api_post("/kb/compile")
        if result:
            remember_task(result.get("task_id"), label="kb_compile", origin="knowledge_base")
            st.success(tr("KB compile queued: {task_id}", task_id=result.get("task_id")))

    if col2.button(tr("Lint KB")):
        result = api_post("/kb/lint")
        if result:
            remember_task(result.get("task_id"), label="kb_lint", origin="knowledge_base")
            st.success(tr("KB lint queued: {task_id}", task_id=result.get("task_id")))

    st.subheader(tr("Master Index"))
    master_index = api_get("/kb/indexes/master", allow_statuses={404})
    if isinstance(master_index, dict):
        if master_index.get("artifact_id"):
            st.success(
                tr(
                    "artifact #{id} {slug}",
                    id=master_index.get("artifact_id"),
                    slug=master_index.get("canonical_slug"),
                )
            )
            if master_index.get("manifest_json"):
                with st.expander(tr("Master Manifest"), expanded=False):
                    st.json(master_index.get("manifest_json"))
        else:
            st.info(master_index.get("message") or tr("No master index artifact yet"))

    st.subheader(tr("Artifacts"))
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
    artifact_search = filter_col5.text_input(tr("Artifact Search"), key="kb_artifact_search")
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
            artifact_rows = []
            for item in items:
                artifact_rows.append(
                    {
                        "id": item.get("id"),
                        "type": item.get("artifact_type"),
                        "title": item.get("title"),
                        "slug": item.get("canonical_slug"),
                        "status": item.get("status"),
                        "review_status": item.get("review_status"),
                        "generator_version": item.get("generator_version"),
                    }
                )
            st.dataframe(pd.DataFrame(artifact_rows), width="stretch", hide_index=True)
        else:
            st.info("No KB artifacts available")

    st.subheader("Artifact Detail")
    current_artifact_options = {
        item["id"]: f"#{item['id']} | {item.get('artifact_type')} | {item.get('title') or 'untitled'}"
        for item in items
        if item.get("id") is not None
    }
    selected_artifact_id = st.selectbox(
        tr("Current Artifact"),
        [None, *list(current_artifact_options)],
        format_func=lambda value: tr("Manual Artifact ID") if value is None else current_artifact_options[value],
        key="current_artifact_id",
    )
    artifact_id = st.number_input("Artifact ID", min_value=1, step=1, key="artifact_id")
    if st.button("Load Artifact"):
        detail = api_get(f"/kb/artifacts/{resolve_artifact_id(artifact_id, selected_artifact_id)}")
        if detail:
            render_kb_artifact_detail(detail)

    st.subheader(tr("Entities"))
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
    entity_search = entity_col3.text_input(tr("Entity Search"), key="kb_entity_search")
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
    current_entity_options = {
        item["id"]: f"#{item['id']} | {item.get('entity_type')} | {item.get('canonical_name') or 'unnamed'}"
        for item in items
        if item.get("id") is not None
    }
    selected_entity_id = st.selectbox(
        tr("Current Entity"),
        [None, *list(current_entity_options)],
        format_func=lambda value: tr("Manual Entity ID") if value is None else current_entity_options[value],
        key="current_entity_id",
    )
    entity_id = st.number_input("Entity ID", min_value=1, step=1, key="kb_entity_id")
    if st.button("Load Entity"):
        entity_detail = api_get(f"/kb/entities/{resolve_entity_id(entity_id, selected_entity_id)}")
        if entity_detail:
            render_entity_detail(entity_detail)

    st.subheader(tr("Conflicts"))
    conflict_col1, conflict_col2 = st.columns(2)
    conflict_artifact_id = conflict_col1.number_input(
        "Conflict Artifact ID Filter",
        min_value=0,
        step=1,
        key="kb_conflict_artifact_id",
        help="0 means no artifact filter",
    )
    conflict_review_filter = conflict_col2.selectbox(
        "Conflict Review Filter",
        ["", "auto", "needs_review", "approved", "rejected"],
        index=0,
        key="kb_conflict_review_filter",
    )
    conflict_params = None
    if conflict_artifact_id > 0:
        conflict_params = {"artifact_id": conflict_artifact_id}
    if conflict_review_filter:
        conflict_params = conflict_params or {}
        conflict_params["review_status"] = conflict_review_filter
    conflicts = api_get("/kb/conflicts", conflict_params)
    if isinstance(conflicts, list):
        if conflicts:
            conflict_rows = []
            for item in conflicts:
                conflict_rows.append(
                    {
                        "conflict_group_id": item.get("conflict_group_id"),
                        "claim_count": item.get("claim_count"),
                        "artifact_ids": ", ".join(
                            str(artifact_id) for artifact_id in item.get("artifact_ids", [])
                        ),
                        "claim_ids": ", ".join(str(claim_id) for claim_id in item.get("claim_ids", [])),
                        "claim_previews": "\n\n".join(item.get("claim_previews", [])),
                    }
                )
            st.dataframe(pd.DataFrame(conflict_rows), width="stretch", hide_index=True)
        else:
            st.info(tr("No KB conflicts detected"))

    st.subheader(tr("Claims"))
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
    claim_search = st.text_input(tr("Claim Search"), key="kb_claim_search")
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
    st.header(tr("Tasks"))

    recent_tasks = st.session_state.get("recent_tasks") or []
    task_origin_options = [""] + sorted(
        {str(item.get("origin", "")) for item in recent_tasks if item.get("origin")}
    )
    selected_origin = st.selectbox(
        tr("Task Origin Filter"),
        task_origin_options,
        format_func=lambda origin_value: tr("All Origins") if not origin_value else tr(origin_value),
        key="task_origin_filter",
    )
    task_label_search = st.text_input(tr("Task Label Search"), key="task_label_search")
    task_sort_order = st.selectbox(
        tr("Task Sort Order"),
        ["newest", "oldest"],
        format_func=lambda sort_value: tr("Newest First") if sort_value == "newest" else tr("Oldest First"),
        key="task_sort_order",
    )
    filtered_recent_tasks = sort_recent_tasks(
        search_recent_tasks(
            filter_recent_tasks(recent_tasks, selected_origin),
            task_label_search,
        ),
        task_sort_order,
    )
    st.subheader(tr("Recent UI Tasks"))
    if filtered_recent_tasks:
        st.dataframe(pd.DataFrame(filtered_recent_tasks), width="stretch", hide_index=True)
        selected_task_id = st.selectbox(
            tr("Tracked Task"),
            [item["task_id"] for item in filtered_recent_tasks],
            format_func=lambda task_value: next(
                (
                    f"{item['task_id']} | {tr(item['label'])} | {tr(item['origin'])}"
                    for item in filtered_recent_tasks
                    if item["task_id"] == task_value
                ),
                task_value,
            ),
            key="tracked_task_id",
        )
        if st.button(tr("Load Selected Task")):
            status = api_get(f"/tasks/{selected_task_id}", {"include_result": True})
            if status:
                st.json(status)
    else:
        st.info(tr("No tracked tasks in this session"))

    selected_task_id = st.selectbox(
        tr("Current Task"),
        [""] + [item["task_id"] for item in filtered_recent_tasks],
        format_func=lambda task_value: tr("Manual Task ID")
        if not task_value
        else next(
            (
                f"{item['task_id']} | {tr(item['label'])} | {tr(item['origin'])}"
                for item in filtered_recent_tasks
                if item["task_id"] == task_value
            ),
            task_value,
        ),
        key="current_task_id",
    )
    task_id = st.text_input(tr("Task ID"))
    include_result = st.checkbox(tr("Include Result"), value=True)
    if st.button(tr("Load Task Status")):
        resolved_task_id = resolve_task_id(task_id, selected_task_id or None)
        if not resolved_task_id:
            st.warning(tr("Enter a task ID"))
        else:
            status = api_get(f"/tasks/{resolved_task_id}", {"include_result": include_result})
            if status:
                st.json(status)


# --- Main ---

def _on_language_change() -> None:
    persist_language(st.session_state["ui_language_selector"])

def main():
    current_language = init_language_state()
    install_streamlit_i18n()

    st.set_page_config(page_title=tr("CR Intelligence Platform"), layout="wide")

    with st.sidebar:
        selected_language = st.selectbox(
            tr("Language"),
            options=list(LANGUAGE_OPTIONS),
            index=list(LANGUAGE_OPTIONS).index(current_language),
            format_func=language_label,
            key="ui_language_selector",
            on_change=_on_language_change,
        )

    if selected_language != current_language:
        persist_language(selected_language)

    st.title(tr("CR Intelligence Platform"))

    pages = {
        "dashboard": ("Dashboard", page_dashboard),
        "documents": ("Documents", page_documents),
        "pipeline": ("Pipeline", page_pipeline),
        "matrix": ("Matrix", page_matrix),
        "reviews": ("Reviews", page_reviews),
        "scoring_models": ("Scoring Models", page_scoring_models),
        "knowledge_base": ("Knowledge Base", page_kb),
        "tasks": ("Tasks", page_tasks),
        "outputs": ("Outputs", page_outputs),
    }

    page = st.sidebar.radio(
        tr("Navigation"),
        list(pages.keys()),
        format_func=lambda page_key: tr(pages[page_key][0]),
        key="navigation_page",
    )
    pages[page][1]()


if __name__ == "__main__":
    main()

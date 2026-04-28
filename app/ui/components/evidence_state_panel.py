"""Evidence state diagnostic panel for Streamlit operator UI.

Renders a per-version evidence density panel and a corpus-level summary
badge. Designed to be embedded in the main document viewer.

Usage:
    from app.ui.components.evidence_state_panel import (
        show_evidence_state_panel,
        show_corpus_evidence_badge,
    )

    # Inside a Streamlit page:
    show_evidence_state_panel(document_id=42, version_id=7, api_base="http://app:8000")
    show_corpus_evidence_badge(api_base="http://app:8000")
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ── Colour/icon mapped to state ─────────────────────────────────────────────
_STATE_META: dict[str, dict[str, str]] = {
    "evidence_rows_present": {
        "icon": "✅",
        "label": "Evidence rows present",
        "colour": "green",
        "help": "This version has pair evidence rows ready for scoring.",
    },
    "healthy_empty_state": {
        "icon": "🟡",
        "label": "Healthy empty state",
        "colour": "orange",
        "help": (
            "Extraction ran but no fragment contained ≥2 distinct MNN mentions. "
            "This is expected for documents without drug substitution comparisons."
        ),
    },
    "degraded_routing": {
        "icon": "🟠",
        "label": "Degraded routing",
        "colour": "orange",
        "help": (
            "Majority of fragments are image/OCR-unavailable. "
            "Text extraction was skipped for those fragments."
        ),
    },
    "extraction_missing": {
        "icon": "🔴",
        "label": "Extraction missing",
        "colour": "red",
        "help": "The extraction stage has not run for this version.",
    },
    "scoring_missing": {
        "icon": "🟤",
        "label": "Scoring missing",
        "colour": "brown",
        "help": "Evidence rows exist but no scored MatrixCell has been computed.",
    },
    "no_mnn": {
        "icon": "⚪",
        "label": "No MNN found",
        "colour": "grey",
        "help": "Extraction ran but zero MNN/INN drug name hits were found.",
    },
    "unknown": {
        "icon": "❓",
        "label": "Unknown",
        "colour": "grey",
        "help": "Evidence state could not be determined.",
    },
}


def _fetch_evidence_state(
    document_id: int, version_id: int, api_base: str
) -> dict[str, Any] | None:
    """Fetch version evidence state from the API. Returns raw dict or None on error."""
    try:
        import requests  # local import — optional in test environments

        url = f"{api_base}/documents/{document_id}/versions/{version_id}/evidence-state"
        resp = requests.get(url, params={"include_fragments": "false"}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch evidence state for version %d: %s", version_id, exc)
        return None


def _fetch_corpus_coverage(api_base: str) -> dict[str, Any] | None:
    """Fetch corpus-level coverage from the API. Returns raw dict or None on error."""
    try:
        import requests

        url = f"{api_base}/documents/corpus/evidence-coverage"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Could not fetch corpus evidence coverage: %s", exc)
        return None


def show_evidence_state_panel(
    document_id: int,
    version_id: int,
    api_base: str = "http://app:8000",
    *,
    expanded: bool = False,
) -> None:
    """Render evidence density state panel for a document version.

    Designed for embedding inside a Streamlit document detail page.

    Parameters
    ----------
    document_id:
        DocumentRegistry.id
    version_id:
        DocumentVersion.id
    api_base:
        Base URL for the backend API (e.g. http://app:8000)
    expanded:
        Whether the expander starts open (default False)
    """
    try:
        import streamlit as st
    except ImportError:
        return  # Not a Streamlit context

    with st.expander("🔬 Evidence Density Diagnostics", expanded=expanded):
        data = _fetch_evidence_state(document_id, version_id, api_base)
        if data is None:
            st.warning("Could not load evidence state (API unavailable).")
            return

        state = data.get("dominant_evidence_state", "unknown")
        meta = _STATE_META.get(state, _STATE_META["unknown"])
        explanation = data.get("explanation", "")

        # State badge
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric(
                label="Evidence State",
                value=f"{meta['icon']} {meta['label']}",
                help=meta["help"],
            )
        with col2:
            st.caption(explanation)

        # Corpus metrics
        st.markdown("---")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Sections", data.get("sections_total", 0))
        m2.metric("Fragments", data.get("fragments_total", 0))
        m3.metric("Fragments w/ MNN ≥2", data.get("fragments_with_mnn", 0))
        m4.metric("OCR-unavailable", data.get("fragments_ocr_unavailable", 0))
        m5.metric("Evidence rows", data.get("pair_evidence_total", 0))

        # Source artifact type
        dom_artifact = data.get("source_artifact_type_dominant")
        if dom_artifact:
            st.caption(f"Dominant source artifact type: **{dom_artifact}**")

        # Extraction ran indicator
        extraction_ran = data.get("extraction_ran", False)
        if not extraction_ran:
            st.error(
                "⚠️ Extraction stage has **not** run for this version. "
                "Evidence cannot be generated until extraction is triggered."
            )
        else:
            st.success("Extraction stage ran successfully for this version.")


def show_corpus_evidence_badge(
    api_base: str = "http://app:8000",
    *,
    show_details: bool = False,
) -> None:
    """Render a compact corpus evidence coverage badge.

    Suitable for a sidebar or dashboard overview panel.
    """
    try:
        import streamlit as st
    except ImportError:
        return

    data = _fetch_corpus_coverage(api_base)
    if data is None:
        st.caption("⚠️ Corpus evidence coverage: unavailable")
        return

    total = data.get("total_current_versions", 0)
    with_evidence = data.get("versions_with_evidence", 0)
    healthy_empty = data.get("versions_healthy_empty", 0)
    missing = data.get("versions_extraction_missing", 0)
    density_pct = data.get("evidence_density_pct", 0.0)

    st.caption(
        f"📊 Corpus: {total} current versions | "
        f"✅ {with_evidence} with evidence | "
        f"🟡 {healthy_empty} healthy empty | "
        f"🔴 {missing} extraction missing | "
        f"density {density_pct:.1f}%"
    )

    if show_details:
        with st.expander("Corpus evidence coverage details", expanded=False):
            st.json(data)


def render_evidence_state_table(state_data: dict[str, Any]) -> None:
    """Render fragment diagnostics as a compact table.

    Accepts the raw JSON response from
    GET /documents/{id}/versions/{vid}/evidence-state
    """
    try:
        import pandas as pd
        import streamlit as st
    except ImportError:
        return

    fragment_diags = state_data.get("fragment_diagnostics", [])
    if not fragment_diags:
        st.caption("No per-fragment diagnostics available (set include_fragments=true).")
        return

    rows = []
    for d in fragment_diags:
        meta = _STATE_META.get(d.get("evidence_state", "unknown"), _STATE_META["unknown"])
        rows.append(
            {
                "Fragment ID": d.get("fragment_id"),
                "Content Kind": d.get("content_kind", ""),
                "Source Type": d.get("source_artifact_type", ""),
                "Source Block": d.get("source_block_id", ""),
                "State": f"{meta['icon']} {meta['label']}",
                "Evidence Rows": d.get("evidence_rows", 0),
                "Preview": (d.get("fragment_text_preview") or "")[:60],
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

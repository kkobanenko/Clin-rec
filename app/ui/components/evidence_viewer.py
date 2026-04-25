"""Evidence viewer component for Streamlit UI."""

import streamlit as st
import pandas as pd
from typing import Any, Dict, Optional


def show_evidence_viewer(
    evidence_data: list[Dict[str, Any]],
    total_count: int,
    page_size: int = 50,
    enable_filters: bool = True,
    container_key: str = "evidence_viewer",
) -> Dict[str, Any]:
    """Render evidence viewer with pagination and filtering.
    
    Args:
        evidence_data: List of evidence records from API
        total_count: Total count of available evidence records
        page_size: Items per page (default 50)
        enable_filters: Show filter controls (default True)
        container_key: Unique key for stateful components
    
    Returns:
        State dict with current page, filters, etc.
    """
    
    if not evidence_data:
        st.info("📋 No evidence found matching current filters")
        return {"state": "empty", "total": total_count}
    
    # Calculate pagination info
    total_pages = (total_count + page_size - 1) // page_size
    current_page = st.session_state.get(f"{container_key}_page", 1)
    
    # Header with stats
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"📊 Showing {len(evidence_data)} of {total_count} evidence rows")
    with col2:
        st.caption(f"Page {current_page} of {total_pages}")
    with col3:
        if st.button("🔄 Refresh", key=f"{container_key}_refresh"):
            st.rerun()
    
    # Optional filters
    if enable_filters:
        with st.expander("🔍 Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_type = st.selectbox(
                    "Relation Type",
                    options=["All"] + list(set(e.get("relation_type", "") for e in evidence_data if e.get("relation_type"))),
                    key=f"{container_key}_filter_type"
                )
            
            with col2:
                min_score = st.slider(
                    "Min Score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    key=f"{container_key}_filter_score"
                )
            
            with col3:
                review_status = st.selectbox(
                    "Review Status",
                    options=["All", "auto", "manual"],
                    key=f"{container_key}_filter_status"
                )
    
    # Data table with selection and details
    st.subheader("Evidence Records")
    
    # Prepare dataframe for display
    df_display = pd.DataFrame(evidence_data)
    
    # Column selection for display
    display_columns = [col for col in [
        "id", "relation_type", "role_score", "final_fragment_score", 
        "review_status", "created_at"
    ] if col in df_display.columns]
    
    if display_columns:
        st.dataframe(
            df_display[display_columns],
            use_container_width=True,
            hide_index=True,
            key=f"{container_key}_table"
        )
    else:
        st.write(df_display)
    
    # Pagination controls
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("◀ Previous", disabled=current_page <= 1, key=f"{container_key}_prev"):
            st.session_state[f"{container_key}_page"] = current_page - 1
            st.rerun()
    
    with col2:
        st.text(f"Page {current_page}/{total_pages}")
    
    with col3:
        if st.button("Next ▶", disabled=current_page >= total_pages, key=f"{container_key}_next"):
            st.session_state[f"{container_key}_page"] = current_page + 1
            st.rerun()
    
    with col4:
        page_input = st.number_input(
            "Go to page",
            min_value=1,
            max_value=total_pages,
            value=current_page,
            step=1,
            key=f"{container_key}_go_to_page"
        )
        if page_input != current_page:
            st.session_state[f"{container_key}_page"] = page_input
            st.rerun()
    
    with col5:
        page_size_new = st.selectbox(
            "Items/page",
            options=[25, 50, 100, 250],
            index=1,
            key=f"{container_key}_page_size"
        )
    
    return {
        "state": "loaded",
        "total": total_count,
        "current_page": current_page,
        "page_size": page_size_new,
        "filter_type": filter_type if enable_filters else None,
        "filter_min_score": min_score if enable_filters else None,
        "filter_status": review_status if enable_filters else None,
    }


def show_evidence_detail(evidence_record: Dict[str, Any]) -> None:
    """Show detailed view of single evidence record.
    
    Args:
        evidence_record: Evidence record dictionary
    """
    
    st.json(evidence_record)
    
    # Show scoring breakdown if available
    scores = {
        k: v for k, v in evidence_record.items()
        if "score" in k.lower() and isinstance(v, (int, float))
    }
    
    if scores:
        st.subheader("Scoring Breakdown")
        st.bar_chart(pd.DataFrame([scores]))


def show_evidence_loading_error(error_response: Dict[str, Any]) -> None:
    """Show error message for failed evidence loading.
    
    Args:
        error_response: Error response from API
    """
    
    error_msg = error_response.get("detail", "Unknown error loading evidence")
    status_code = error_response.get("status_code", "")
    
    st.error(f"❌ Failed to load evidence{f' ({status_code})' if status_code else ''}: {error_msg}")
    
    with st.expander("Debug info"):
        st.json(error_response)


def show_evidence_empty_state(document_id: int, reason: str = "no_evidence") -> None:
    """Show appropriate empty state for evidence.
    
    Args:
        document_id: Document ID
        reason: Reason for empty state ("no_evidence", "not_indexed", "error")
    """
    
    messages = {
        "no_evidence": f"📭 No evidence extracted yet for document {document_id}. Evidence will appear after full pipeline execution.",
        "not_indexed": f"⏳ Document {document_id} is being indexed. Evidence will appear after processing completes.",
        "error": f"❌ Error loading evidence for document {document_id}. Please try again or contact support.",
    }
    
    st.info(messages.get(reason, messages["no_evidence"]))

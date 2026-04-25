"""Tests for evidence viewer Streamlit component."""

import pytest
from app.ui.components.evidence_viewer import (
    show_evidence_viewer,
    show_evidence_detail,
    show_evidence_loading_error,
    show_evidence_empty_state,
)


def test_evidence_viewer_signatures_correct():
    """Test that component functions have correct signatures."""
    import inspect
    
    # Verify show_evidence_viewer exists and has correct params
    sig = inspect.signature(show_evidence_viewer)
    params = list(sig.parameters.keys())
    assert 'evidence_data' in params
    assert 'total_count' in params
    assert 'page_size' in params


def test_evidence_detail_callable():
    """Test evidence detail viewer is callable."""
    assert callable(show_evidence_detail)


def test_error_display_callable():
    """Test error display is callable."""
    assert callable(show_evidence_loading_error)


def test_empty_state_callable():
    """Test empty state display is callable."""
    assert callable(show_evidence_empty_state)

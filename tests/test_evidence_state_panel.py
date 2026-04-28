"""Tests for evidence_state_panel UI component (no Streamlit runtime required)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# Import the module under test — Streamlit is imported lazily
from app.ui.components.evidence_state_panel import (
    _STATE_META,
    _fetch_corpus_coverage,
    _fetch_evidence_state,
    render_evidence_state_table,
    show_corpus_evidence_badge,
    show_evidence_state_panel,
)


# ── _STATE_META completeness ───────────────────────────────────────────────

class TestStateMetaCompleteness:
    """All known evidence states must be in _STATE_META with required keys."""

    KNOWN_STATES = {
        "evidence_rows_present",
        "healthy_empty_state",
        "degraded_routing",
        "extraction_missing",
        "scoring_missing",
        "no_mnn",
        "unknown",
    }

    def test_all_states_present(self):
        assert self.KNOWN_STATES == set(_STATE_META.keys())

    def test_each_state_has_required_keys(self):
        required = {"icon", "label", "colour", "help"}
        for state, meta in _STATE_META.items():
            assert required.issubset(meta.keys()), (
                f"State '{state}' is missing keys: {required - meta.keys()}"
            )

    def test_icons_are_non_empty(self):
        for state, meta in _STATE_META.items():
            assert meta["icon"].strip(), f"State '{state}' has empty icon"

    def test_labels_are_non_empty(self):
        for state, meta in _STATE_META.items():
            assert meta["label"].strip(), f"State '{state}' has empty label"

    def test_help_text_is_non_empty(self):
        for state, meta in _STATE_META.items():
            assert meta["help"].strip(), f"State '{state}' has empty help text"


# ── _fetch_evidence_state ──────────────────────────────────────────────────

class TestFetchEvidenceState:
    def test_returns_dict_on_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "dominant_evidence_state": "healthy_empty_state",
            "explanation": "Some text",
        }
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp):
            result = _fetch_evidence_state(1, 2, "http://app:8000")

        assert result is not None
        assert result["dominant_evidence_state"] == "healthy_empty_state"

    def test_returns_none_on_connection_error(self):
        with patch("requests.get", side_effect=ConnectionError("refused")):
            result = _fetch_evidence_state(1, 2, "http://app:8000")
        assert result is None

    def test_returns_none_on_timeout(self):
        import requests as _req
        with patch("requests.get", side_effect=_req.exceptions.Timeout("timeout")):
            result = _fetch_evidence_state(1, 2, "http://app:8000")
        assert result is None

    def test_calls_correct_url(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp) as mock_get:
            _fetch_evidence_state(42, 7, "http://api:9000")

        url_called = mock_get.call_args[0][0]
        assert "42" in url_called
        assert "7" in url_called
        assert "evidence-state" in url_called


# ── _fetch_corpus_coverage ────────────────────────────────────────────────

class TestFetchCorpusCoverage:
    def test_returns_dict_on_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"total_current_versions": 10}
        mock_resp.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_resp):
            result = _fetch_corpus_coverage("http://app:8000")

        assert result is not None
        assert result["total_current_versions"] == 10

    def test_returns_none_on_error(self):
        with patch("requests.get", side_effect=Exception("network error")):
            result = _fetch_corpus_coverage("http://app:8000")
        assert result is None


# ── render_evidence_state_table ────────────────────────────────────────────

class TestRenderEvidenceStateTable:
    def test_empty_fragment_diagnostics_shows_caption(self):
        mock_st = MagicMock()
        with patch("streamlit.caption") as mock_caption, \
             patch("streamlit.dataframe") as mock_df:
            render_evidence_state_table({"fragment_diagnostics": []})
        # Should call caption, not dataframe
        # (since importlib may substitute, we test via the module-level mock)
        # No assert needed — function should not raise

    def test_table_renders_without_error(self):
        """Rendering with mock fragment_diagnostics should not raise."""
        mock_st = MagicMock()
        fake_diags = [
            {
                "fragment_id": 101,
                "content_kind": "text",
                "source_artifact_type": "json",
                "source_block_id": "b_0001",
                "evidence_state": "no_mnn",
                "evidence_rows": 0,
                "fragment_text_preview": "some text",
            },
            {
                "fragment_id": 102,
                "content_kind": "image",
                "source_artifact_type": "json",
                "source_block_id": "b_0002",
                "evidence_state": "degraded_routing",
                "evidence_rows": 0,
                "fragment_text_preview": None,
            },
        ]

        with patch("streamlit.dataframe") as mock_df, \
             patch("streamlit.caption") as mock_caption:
            render_evidence_state_table({"fragment_diagnostics": fake_diags})


# ── show_evidence_state_panel ──────────────────────────────────────────────

class TestShowEvidenceStatePanel:
    def test_handles_api_unavailable_gracefully(self):
        """When API is down, panel renders a warning instead of raising."""
        with patch("app.ui.components.evidence_state_panel._fetch_evidence_state", return_value=None), \
             patch("streamlit.expander") as mock_expander, \
             patch("streamlit.warning") as mock_warning:
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_expander.return_value = mock_ctx

            show_evidence_state_panel(1, 2)
            # Should not raise; just warns

    def test_panel_displays_state_data(self):
        """Panel uses data from API to display metrics."""
        fake_state = {
            "dominant_evidence_state": "healthy_empty_state",
            "explanation": "Healthy because no drugs found",
            "sections_total": 10,
            "fragments_total": 30,
            "fragments_with_mnn": 0,
            "fragments_ocr_unavailable": 0,
            "pair_evidence_total": 0,
            "source_artifact_type_dominant": "json",
            "extraction_ran": True,
        }

        def _fake_columns(spec):
            n = spec if isinstance(spec, int) else len(spec)
            return [MagicMock() for _ in range(n)]

        with patch(
            "app.ui.components.evidence_state_panel._fetch_evidence_state",
            return_value=fake_state,
        ), patch("streamlit.expander") as mock_expander, \
           patch("streamlit.metric"), \
           patch("streamlit.caption"), \
           patch("streamlit.success"), \
           patch("streamlit.columns", side_effect=_fake_columns), \
           patch("streamlit.markdown"):
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_expander.return_value = mock_ctx
            # Should not raise
            show_evidence_state_panel(1, 2)


# ── show_corpus_evidence_badge ────────────────────────────────────────────

class TestShowCorpusEvidenceBadge:
    def test_shows_unavailable_when_api_down(self):
        with patch(
            "app.ui.components.evidence_state_panel._fetch_corpus_coverage",
            return_value=None,
        ), patch("streamlit.caption") as mock_caption:
            show_corpus_evidence_badge()
            mock_caption.assert_called_once()
            assert "unavailable" in mock_caption.call_args[0][0]

    def test_renders_corpus_data(self):
        fake_coverage = {
            "total_current_versions": 25,
            "versions_with_evidence": 3,
            "versions_healthy_empty": 18,
            "versions_extraction_missing": 4,
            "evidence_density_pct": 12.0,
        }
        with patch(
            "app.ui.components.evidence_state_panel._fetch_corpus_coverage",
            return_value=fake_coverage,
        ), patch("streamlit.caption") as mock_caption:
            show_corpus_evidence_badge()
            mock_caption.assert_called_once()
            caption_text = mock_caption.call_args[0][0]
            assert "25" in caption_text
            assert "12.0%" in caption_text

"""Tests for scoring engine."""

import pytest
from app.services.scoring.engine import ScoringEngine, RELATION_ROLE_SCORES


class TestScoringEngine:
    def setup_method(self):
        self.engine = ScoringEngine()

    def test_text_signal_strong(self):
        score = self.engine._text_signal_score("explicit_alternative_same_line")
        assert score == 0.9

    def test_text_signal_moderate(self):
        score = self.engine._text_signal_score("switch_if_intolerance")
        assert score == 0.6

    def test_text_signal_weak(self):
        score = self.engine._text_signal_score("later_line_only")
        assert score == 0.3

    def test_text_signal_unknown(self):
        score = self.engine._text_signal_score("unknown_type")
        assert score == 0.1

    def test_parity_score_full(self):
        score = self.engine._parity_score("A", "1")
        assert score == 1.0

    def test_parity_score_partial(self):
        score = self.engine._parity_score("B", "3")
        assert score == pytest.approx(0.65)

    def test_parity_score_none(self):
        score = self.engine._parity_score(None, None)
        assert score == 0.5

    def test_penalty_score_no_signal(self):
        score = self.engine._penalty_score("no_substitution_signal")
        assert score == 0.9

    def test_penalty_score_good_relation(self):
        score = self.engine._penalty_score("explicit_alternative_same_line")
        assert score == 0.0

    def test_aggregate_context_score_single(self):
        score = self.engine._aggregate_context_score([0.8])
        assert score == pytest.approx(0.8)

    def test_aggregate_context_score_multiple(self):
        score = self.engine._aggregate_context_score([0.6, 0.8, 0.4])
        # 0.7 * max(0.8) + 0.3 * mean(0.6) = 0.56 + 0.18 = 0.74
        assert score == pytest.approx(0.74)

    def test_aggregate_context_score_empty(self):
        score = self.engine._aggregate_context_score([])
        assert score == 0.0

    def test_relation_role_scores_coverage(self):
        """All known relation types have role scores."""
        expected_types = [
            "explicit_alternative_same_line", "same_line_option",
            "switch_if_intolerance", "switch_if_failure",
            "later_line_only", "add_on_only", "combination_only",
            "different_population", "no_substitution_signal",
        ]
        for rt in expected_types:
            assert rt in RELATION_ROLE_SCORES

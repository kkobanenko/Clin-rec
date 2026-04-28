"""Tests for scoring engine."""

from types import SimpleNamespace

import pytest
from app.services.matrix_builder import MatrixBuilder
from app.services.scoring.engine import (
    CONTENT_KIND_MULTIPLIER,
    RELATION_ROLE_SCORES,
    ScoringEngine,
)


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

    def test_context_explanation_includes_evidence_and_fragment_ids(self):
        explanation = self.engine._build_context_explanation(
            [
                SimpleNamespace(id=11, fragment_id=101, relation_type="same_line_option"),
                SimpleNamespace(id=12, fragment_id=102, relation_type="switch_if_failure"),
            ],
            [0.8, 0.6],
        )

        assert explanation["evidence_ids"] == [11, 12]
        assert explanation["fragment_ids"] == [101, 102]
        assert explanation["relation_types"] == ["same_line_option", "switch_if_failure"]


class TestMatrixBuilder:
    def test_matrix_explanation_includes_pair_context_and_evidence_ids(self):
        builder = MatrixBuilder()
        explanation = builder._build_matrix_explanation(
            [
                SimpleNamespace(
                    id=21,
                    context_id=7,
                    substitution_score=0.8,
                    confidence_score=0.7,
                    evidence_count=2,
                    explanation_json={"evidence_ids": [11, 12], "fragment_ids": [101, 102]},
                ),
                SimpleNamespace(
                    id=22,
                    context_id=8,
                    substitution_score=0.6,
                    confidence_score=0.5,
                    evidence_count=1,
                    explanation_json={"evidence_ids": [13], "fragment_ids": [103]},
                ),
            ]
        )

        assert explanation["pair_context_score_ids"] == [21, 22]
        assert explanation["contexts"][0]["evidence_ids"] == [11, 12]
        assert explanation["contexts"][1]["fragment_ids"] == [103]


class TestScoringEngineContentKind:
    """Tests for content-kind-aware scoring additions."""

    def setup_method(self):
        self.engine = ScoringEngine()

    def test_practical_score_text(self):
        assert self.engine._practical_score("text") == 0.8

    def test_practical_score_html(self):
        assert self.engine._practical_score("html") == 0.8

    def test_practical_score_table_like(self):
        assert self.engine._practical_score("table_like") == 0.6

    def test_practical_score_unknown(self):
        assert self.engine._practical_score("unknown") == 0.5

    def test_practical_score_image_is_zero(self):
        assert self.engine._practical_score("image") == 0.0

    def test_practical_score_none_defaults_text(self):
        # None or empty → the method treats it as "text" (or "unknown") defaulting to mapped value
        result = self.engine._practical_score(None)  # type: ignore[arg-type]
        assert result in {0.5, 0.8}  # either "unknown" or "text" default is acceptable

    def test_content_kind_multiplier_table(self):
        assert CONTENT_KIND_MULTIPLIER["text"] == 1.0
        assert CONTENT_KIND_MULTIPLIER["html"] == 1.0
        assert CONTENT_KIND_MULTIPLIER["image"] == 0.0

    def test_score_fragment_image_final_is_zero(self):
        ev = SimpleNamespace(
            relation_type="explicit_alternative_same_line",
            uur="A",
            udd="1",
        )
        weights = {
            "role": 0.20, "text": 0.25, "population": 0.15,
            "parity": 0.15, "practical": 0.10, "penalty": 0.15,
        }
        result = self.engine._score_fragment(ev, weights, content_kind="image")
        assert result["final"] == 0.0

    def test_score_fragment_text_positive(self):
        ev = SimpleNamespace(
            relation_type="explicit_alternative_same_line",
            uur="A",
            udd="1",
        )
        weights = {
            "role": 0.20, "text": 0.25, "population": 0.15,
            "parity": 0.15, "practical": 0.10, "penalty": 0.15,
        }
        result = self.engine._score_fragment(ev, weights, content_kind="text")
        assert result["final"] > 0.0
        assert result["final"] <= 1.0

    def test_score_fragment_table_like_lower_than_text(self):
        ev = SimpleNamespace(
            relation_type="explicit_alternative_same_line",
            uur="A",
            udd="1",
        )
        weights = {
            "role": 0.20, "text": 0.25, "population": 0.15,
            "parity": 0.15, "practical": 0.10, "penalty": 0.15,
        }
        text_result = self.engine._score_fragment(ev, weights, content_kind="text")
        table_result = self.engine._score_fragment(ev, weights, content_kind="table_like")
        assert table_result["final"] <= text_result["final"]

    def test_score_fragment_has_all_component_keys(self):
        ev = SimpleNamespace(
            relation_type="same_line_option",
            uur="B",
            udd="2",
        )
        weights = {
            "role": 0.20, "text": 0.25, "population": 0.15,
            "parity": 0.15, "practical": 0.10, "penalty": 0.15,
        }
        result = self.engine._score_fragment(ev, weights)
        expected_keys = {"role", "text", "population", "parity", "practical", "penalty", "final"}
        assert expected_keys == set(result.keys())

    def test_score_fragment_final_in_unit_interval(self):
        for rel in RELATION_ROLE_SCORES:
            for ck in ("text", "html", "table_like", "image", "unknown"):
                ev = SimpleNamespace(relation_type=rel, uur="A", udd="1")
                weights = {
                    "role": 0.20, "text": 0.25, "population": 0.15,
                    "parity": 0.15, "practical": 0.10, "penalty": 0.15,
                }
                result = self.engine._score_fragment(ev, weights, content_kind=ck)
                assert 0.0 <= result["final"] <= 1.0, (
                    f"final={result['final']} out of [0,1] for rel={rel}, ck={ck}"
                )


"""Tests for confidence calculator."""

import pytest
from app.services.scoring.confidence import ConfidenceCalculator


class TestConfidenceCalculator:
    def setup_method(self):
        self.calc = ConfidenceCalculator()

    def test_basic_confidence(self):
        score = self.calc.calculate(
            evidence_count=3,
            fragment_scores=[0.7, 0.8, 0.75],
            relation_types=["explicit_alternative_same_line"] * 3,
        )
        assert 0 <= score <= 1

    def test_single_evidence_lower_confidence(self):
        single = self.calc.calculate(
            evidence_count=1,
            fragment_scores=[0.8],
            relation_types=["explicit_alternative_same_line"],
        )
        multi = self.calc.calculate(
            evidence_count=5,
            fragment_scores=[0.8, 0.75, 0.82, 0.79, 0.81],
            relation_types=["explicit_alternative_same_line"] * 5,
        )
        assert single < multi

    def test_inconsistent_scores_lower_confidence(self):
        consistent = self.calc.calculate(
            evidence_count=3,
            fragment_scores=[0.8, 0.79, 0.81],
            relation_types=["same_line_option"] * 3,
        )
        inconsistent = self.calc.calculate(
            evidence_count=3,
            fragment_scores=[0.1, 0.9, 0.5],
            relation_types=["same_line_option"] * 3,
        )
        assert consistent > inconsistent

    def test_mixed_relation_types_lower_confidence(self):
        uniform = self.calc.calculate(
            evidence_count=3,
            fragment_scores=[0.7, 0.7, 0.7],
            relation_types=["same_line_option"] * 3,
        )
        mixed = self.calc.calculate(
            evidence_count=3,
            fragment_scores=[0.7, 0.7, 0.7],
            relation_types=["same_line_option", "switch_if_intolerance", "later_line_only"],
        )
        assert uniform > mixed

    def test_with_reviewer_agreements(self):
        score = self.calc.calculate(
            evidence_count=3,
            fragment_scores=[0.7, 0.8, 0.75],
            relation_types=["same_line_option"] * 3,
            reviewer_agreements=[True, True, True],
        )
        assert score > 0.5

    def test_confidence_bounds(self):
        score = self.calc.calculate(
            evidence_count=0,
            fragment_scores=[],
            relation_types=[],
        )
        assert 0 <= score <= 1

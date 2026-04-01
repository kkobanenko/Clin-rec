"""Scoring engine — calculates fragment, context, and global scores for MNN pairs."""

import logging
from collections import defaultdict

from app.core.sync_database import get_sync_session
from app.models.evidence import PairContextScore, PairEvidence
from app.models.scoring import ScoringModelVersion
from app.services.scoring.confidence import ConfidenceCalculator

logger = logging.getLogger(__name__)

# Default component weights for scoring model v1
DEFAULT_WEIGHTS = {
    "role": 0.20,
    "text": 0.25,
    "population": 0.15,
    "parity": 0.15,
    "practical": 0.10,
    "penalty": 0.15,
}

# Relation type -> base role score mapping
RELATION_ROLE_SCORES = {
    "explicit_alternative_same_line": 0.95,
    "same_line_option": 0.85,
    "switch_if_intolerance": 0.70,
    "switch_if_failure": 0.65,
    "later_line_only": 0.40,
    "add_on_only": 0.25,
    "combination_only": 0.20,
    "different_population": 0.30,
    "no_substitution_signal": 0.05,
}

# UUR -> parity score (higher is better evidence)
UUR_PARITY = {"A": 1.0, "B": 0.7, "C": 0.4}
UDD_PARITY = {"1": 1.0, "2": 0.8, "3": 0.6, "4": 0.4, "5": 0.2}


class ScoringEngine:
    def __init__(self):
        self.confidence_calculator = ConfidenceCalculator()

    def score_all(self, model_version_id: int) -> int:
        """Score all pairs for a given model version. Returns count of scored pairs."""
        session = get_sync_session()
        try:
            model = session.get(ScoringModelVersion, model_version_id)
            if not model:
                logger.error("ScoringModelVersion %d not found", model_version_id)
                return 0

            weights = model.weights_json or DEFAULT_WEIGHTS

            # Get all evidence grouped by (context, from, to)
            evidence_records = session.query(PairEvidence).filter(
                PairEvidence.review_status != "rejected"
            ).all()

            grouped: dict[tuple[int, int, int], list[PairEvidence]] = defaultdict(list)
            for e in evidence_records:
                key = (e.context_id, e.molecule_from_id, e.molecule_to_id)
                grouped[key].append(e)

            count = 0
            for (ctx_id, mol_from, mol_to), evidence_list in grouped.items():
                # Score each fragment-level evidence
                fragment_scores = []
                for ev in evidence_list:
                    frag_score = self._score_fragment(ev, weights)
                    ev.role_score = frag_score["role"]
                    ev.text_score = frag_score["text"]
                    ev.population_score = frag_score["population"]
                    ev.parity_score = frag_score["parity"]
                    ev.practical_score = frag_score["practical"]
                    ev.penalty = frag_score["penalty"]
                    ev.final_fragment_score = frag_score["final"]
                    fragment_scores.append(frag_score["final"])

                # Aggregate to context level
                if fragment_scores:
                    sub_score = self._aggregate_context_score(fragment_scores)
                    conf_score = self.confidence_calculator.calculate(
                        evidence_count=len(evidence_list),
                        fragment_scores=fragment_scores,
                        relation_types=[e.relation_type for e in evidence_list],
                    )

                    explanation = {
                        "evidence_count": len(evidence_list),
                        "fragment_scores": fragment_scores,
                        "relation_types": [e.relation_type for e in evidence_list],
                        "aggregation": "weighted_max",
                    }

                    # Upsert PairContextScore
                    existing = (
                        session.query(PairContextScore)
                        .filter_by(
                            model_version_id=model_version_id,
                            context_id=ctx_id,
                            molecule_from_id=mol_from,
                            molecule_to_id=mol_to,
                        )
                        .first()
                    )

                    if existing:
                        existing.substitution_score = sub_score
                        existing.confidence_score = conf_score
                        existing.evidence_count = len(evidence_list)
                        existing.explanation_json = explanation
                    else:
                        pcs = PairContextScore(
                            model_version_id=model_version_id,
                            context_id=ctx_id,
                            molecule_from_id=mol_from,
                            molecule_to_id=mol_to,
                            substitution_score=sub_score,
                            confidence_score=conf_score,
                            evidence_count=len(evidence_list),
                            explanation_json=explanation,
                        )
                        session.add(pcs)

                    count += 1

            session.commit()
            logger.info("Scored %d context pairs for model version %d", count, model_version_id)
            return count

        finally:
            session.close()

    def _score_fragment(self, evidence: PairEvidence, weights: dict) -> dict:
        """Compute component scores and weighted final score for a single evidence record."""
        role = RELATION_ROLE_SCORES.get(evidence.relation_type, 0.5)
        text = self._text_signal_score(evidence.relation_type)
        population = 0.5  # Default; would need population overlap analysis
        parity = self._parity_score(evidence.uur, evidence.udd)
        practical = 0.5  # Default; would need practical similarity data
        penalty = self._penalty_score(evidence.relation_type)

        w = weights
        final = (
            w.get("role", 0.2) * role
            + w.get("text", 0.25) * text
            + w.get("population", 0.15) * population
            + w.get("parity", 0.15) * parity
            + w.get("practical", 0.1) * practical
            - w.get("penalty", 0.15) * penalty
        )
        final = max(0.0, min(1.0, final))

        return {
            "role": round(role, 4),
            "text": round(text, 4),
            "population": round(population, 4),
            "parity": round(parity, 4),
            "practical": round(practical, 4),
            "penalty": round(penalty, 4),
            "final": round(final, 4),
        }

    def _text_signal_score(self, relation_type: str) -> float:
        """How strong is the textual signal for substitutability."""
        strong = {"explicit_alternative_same_line", "same_line_option"}
        moderate = {"switch_if_intolerance", "switch_if_failure"}
        weak = {"later_line_only", "add_on_only", "combination_only", "different_population"}

        if relation_type in strong:
            return 0.9
        if relation_type in moderate:
            return 0.6
        if relation_type in weak:
            return 0.3
        return 0.1

    def _parity_score(self, uur: str | None, udd: str | None) -> float:
        """Score based on evidence parity (UUR/UDD)."""
        uur_s = UUR_PARITY.get(uur, 0.5) if uur else 0.5
        udd_s = UDD_PARITY.get(udd, 0.5) if udd else 0.5
        return (uur_s + udd_s) / 2

    def _penalty_score(self, relation_type: str) -> float:
        """Penalty for non-substitutable relationship types."""
        penalties = {
            "no_substitution_signal": 0.9,
            "combination_only": 0.6,
            "add_on_only": 0.5,
            "different_population": 0.4,
            "later_line_only": 0.3,
        }
        return penalties.get(relation_type, 0.0)

    def _aggregate_context_score(self, fragment_scores: list[float]) -> float:
        """Aggregate fragment scores to a context-level substitution score."""
        if not fragment_scores:
            return 0.0
        # Weighted max: 70% max + 30% mean
        max_score = max(fragment_scores)
        mean_score = sum(fragment_scores) / len(fragment_scores)
        return round(0.7 * max_score + 0.3 * mean_score, 4)

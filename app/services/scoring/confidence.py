"""Confidence calculator — computes confidence score separately from substitution score."""

import logging
import statistics

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    def calculate(
        self,
        evidence_count: int,
        fragment_scores: list[float],
        relation_types: list[str],
        reviewer_agreements: list[bool] | None = None,
    ) -> float:
        """Calculate confidence score for a pair-context.

        Confidence is independent of substitution score and reflects
        how much we trust the computed score.

        Args:
            evidence_count: Number of evidence records
            fragment_scores: Individual fragment-level scores
            relation_types: Relation types from evidence
            reviewer_agreements: If available, list of reviewer agree/disagree signals

        Returns:
            Confidence score between 0 and 1
        """
        components = []

        # 1. Evidence volume component (more evidence = higher confidence)
        volume_score = min(evidence_count / 5.0, 1.0)  # Saturates at 5 evidence records
        components.append(("volume", volume_score, 0.25))

        # 2. Score consistency (low variance = higher confidence)
        if len(fragment_scores) > 1:
            try:
                stdev = statistics.stdev(fragment_scores)
                consistency = max(0, 1.0 - stdev * 2)
            except statistics.StatisticsError:
                consistency = 0.5
        else:
            consistency = 0.6  # Single evidence — moderate confidence
        components.append(("consistency", consistency, 0.25))

        # 3. Relation type agreement (same type across evidence = higher confidence)
        if relation_types:
            unique_types = set(relation_types)
            type_agreement = 1.0 / len(unique_types)
            if len(unique_types) == 1:
                type_agreement = 1.0
            elif len(unique_types) == 2:
                type_agreement = 0.6
            else:
                type_agreement = 0.3
        else:
            type_agreement = 0.3
        components.append(("type_agreement", type_agreement, 0.25))

        # 4. Reviewer agreement (if available)
        if reviewer_agreements:
            agree_rate = sum(1 for a in reviewer_agreements if a) / len(reviewer_agreements)
            components.append(("reviewer", agree_rate, 0.25))
        else:
            # No reviewer input — moderate confidence on this dimension
            components.append(("reviewer", 0.5, 0.25))

        # Weighted sum
        total_weight = sum(w for _, _, w in components)
        confidence = sum(score * weight for _, score, weight in components) / total_weight

        return round(max(0.0, min(1.0, confidence)), 4)

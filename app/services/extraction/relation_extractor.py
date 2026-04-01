"""Relation signal extractor — finds textual signals of substitutability, alternatives, and switches between MNN."""

import logging
import re

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "relation_v1.0"

# Relation signal patterns mapped to relation taxonomy types
RELATION_RULES: list[tuple[str, str, float]] = [
    # (regex pattern, relation_type, base_confidence)

    # Explicit alternative same line
    (r"(?:или|либо)\s+\w+", "explicit_alternative_same_line", 0.7),
    (r"(?:альтернатив(?:ой|ой\s+является|но|ный\s+(?:вариант|препарат)))", "explicit_alternative_same_line", 0.85),
    (r"(?:в\s+качестве\s+альтернатив)", "explicit_alternative_same_line", 0.85),
    (r"(?:может\s+(?:быть\s+)?замен[её]н)", "explicit_alternative_same_line", 0.85),
    (r"(?:взаимозамен)", "explicit_alternative_same_line", 0.8),

    # Same-line option
    (r"(?:наравне\s+с|наряду\s+с|так(?:же|ой\s+же)\s+эффективност)", "same_line_option", 0.75),
    (r"(?:равноценн|эквивалент)", "same_line_option", 0.8),

    # Switch if intolerance
    (r"(?:при\s+непереносимости|в\s+случае\s+непереносимости|при\s+аллерги)", "switch_if_intolerance", 0.85),
    (r"(?:при\s+(?:наличии\s+)?противопоказани[ийях])", "switch_if_intolerance", 0.8),
    (r"(?:при\s+(?:развитии\s+)?побочн(?:ых|ого))", "switch_if_intolerance", 0.75),

    # Switch if failure
    (r"(?:при\s+неэффективности|при\s+отсутствии\s+эффекта)", "switch_if_failure", 0.85),
    (r"(?:при\s+недостаточн(?:ой|ом)\s+(?:эффект|ответ))", "switch_if_failure", 0.8),
    (r"(?:в\s+случае\s+неэффективности|при\s+неудаче)", "switch_if_failure", 0.8),
    (r"(?:при\s+рефрактерн)", "switch_if_failure", 0.8),

    # Later line only
    (r"(?:(?:второй|третьей|следующей|последующей)\s+лини[ияе])", "later_line_only", 0.7),
    (r"(?:резервн(?:ый|ая|ое)\s+(?:препарат|терапи|средство))", "later_line_only", 0.75),

    # Add-on only
    (r"(?:в\s+(?:дополнение|добавление)\s+к)", "add_on_only", 0.8),
    (r"(?:дополнительно\s+(?:к|назначить))", "add_on_only", 0.75),

    # Combination only
    (r"(?:в\s+комбинации\s+с|в\s+сочетании\s+с)", "combination_only", 0.8),
    (r"(?:комбинированн(?:ая|ое|ый)\s+(?:терапи|лечени|схем))", "combination_only", 0.75),

    # Different population
    (r"(?:только\s+(?:у|для)\s+(?:детей|взрослых|пожилых|беременных|женщин|мужчин))", "different_population", 0.8),
    (r"(?:противопоказан\s+(?:у|для)\s+(?:детей|беременных))", "different_population", 0.8),

    # No substitution signal
    (r"(?:не\s+рекомендуется|не\s+рекомендовано|не\s+следует)", "no_substitution_signal", 0.75),
    (r"(?:не\s+является\s+(?:заменой|альтернатив))", "no_substitution_signal", 0.85),
    (r"(?:не\s+может\s+(?:замен|быть\s+использован\s+вместо))", "no_substitution_signal", 0.85),
]


class RelationExtractor:
    def extract(self, text: str, molecule_ids: list[int] | None = None) -> list[dict]:
        """Extract relation signals from text.

        Args:
            text: Fragment text to analyze
            molecule_ids: If provided, only return relations involving these molecules

        Returns:
            List of {"relation_type": str, "signal_text": str, "confidence": float, "span": (start, end)}
        """
        results = []
        seen = set()

        for pattern, relation_type, confidence in RELATION_RULES:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                key = (relation_type, match.start())
                if key not in seen:
                    seen.add(key)

                    # Extract surrounding context (up to 100 chars on each side)
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end]

                    results.append({
                        "relation_type": relation_type,
                        "signal_text": match.group(),
                        "context_text": context,
                        "confidence": confidence,
                        "span": (match.start(), match.end()),
                        "extractor_version": EXTRACTOR_VERSION,
                    })

        return results

    def classify_relation(self, signals: list[dict]) -> tuple[str, float]:
        """Given multiple signals from a fragment, return the dominant relation type and combined confidence."""
        if not signals:
            return "no_substitution_signal", 0.5

        # Count by type, weighted by confidence
        type_scores: dict[str, float] = {}
        for s in signals:
            rt = s["relation_type"]
            type_scores[rt] = type_scores.get(rt, 0) + s["confidence"]

        best_type = max(type_scores, key=type_scores.get)  # type: ignore[arg-type]
        best_confidence = min(type_scores[best_type] / len([s for s in signals if s["relation_type"] == best_type]), 1.0)

        return best_type, best_confidence

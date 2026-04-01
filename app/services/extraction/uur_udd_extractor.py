"""UUR/UDD extractor — extracts recommendation strength (УУР) and evidence level (УДД) from text."""

import logging
import re

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "uur_udd_v1.0"

# Patterns for УУР (Уровень убедительности рекомендаций)
UUR_PATTERNS = [
    r"УУР\s*[-—–:]\s*([A-CА-С1-3])",
    r"[Уу]ровень\s+убедительности\s+(?:рекомендаци[ий])?\s*[-—–:.]?\s*([A-CА-С])",
    r"(?:Сила|Класс)\s+рекомендаци[ий]\s*[-—–:.]?\s*([A-CА-С1-3I]+)",
    r"\(УУР\s*[-—–]?\s*([A-CА-С])\)",
]

# Patterns for УДД (Уровень достоверности доказательств)
UDD_PATTERNS = [
    r"УДД\s*[-—–:]\s*([1-5])",
    r"[Уу]ровень\s+достоверности\s+(?:доказательств)?\s*[-—–:.]?\s*([1-5])",
    r"[Уу]ровень\s+доказательности?\s*[-—–:.]?\s*([1-5])",
    r"\(УДД\s*[-—–]?\s*([1-5])\)",
]

# Combined pattern for table rows like "УУР A, УДД 1" or "A 1"
COMBINED_PATTERN = re.compile(
    r"УУР\s*[-—–:]?\s*([A-CА-С])\s*[,;]?\s*УДД\s*[-—–:]?\s*([1-5])",
    re.IGNORECASE,
)


class UurUddExtractor:
    def extract(self, text: str) -> list[dict]:
        """Extract UUR/UDD pairs from text.

        Returns list of {"uur": str | None, "udd": str | None, "span": (start, end), "confidence": float}
        """
        results = []

        # Try combined pattern first
        for match in COMBINED_PATTERN.finditer(text):
            uur = self._normalize_uur(match.group(1))
            udd = match.group(2)
            results.append({
                "uur": uur,
                "udd": udd,
                "span": (match.start(), match.end()),
                "confidence": 0.95,
                "extractor_version": EXTRACTOR_VERSION,
            })

        # If no combined matches, try individual patterns
        if not results:
            uur_val = self._find_first(text, UUR_PATTERNS)
            udd_val = self._find_first(text, UDD_PATTERNS)
            if uur_val or udd_val:
                results.append({
                    "uur": self._normalize_uur(uur_val) if uur_val else None,
                    "udd": udd_val,
                    "span": (0, len(text)),
                    "confidence": 0.8,
                    "extractor_version": EXTRACTOR_VERSION,
                })

        return results

    def _find_first(self, text: str, patterns: list[str]) -> str | None:
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def _normalize_uur(self, value: str | None) -> str | None:
        """Normalize Cyrillic letters to Latin equivalents."""
        if not value:
            return None
        mapping = {"А": "A", "В": "B", "С": "C"}
        return mapping.get(value, value).upper()

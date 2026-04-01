"""Disease-context extractor — determines disease, line of therapy, treatment goal, and population constraints."""

import hashlib
import logging
import re

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "context_v1.0"

# Common therapy line patterns in Russian clinical recommendations
LINE_PATTERNS = [
    (r"перв(?:ая|ой)\s+лини[яи]", "1-я линия"),
    (r"втор(?:ая|ой)\s+лини[яи]", "2-я линия"),
    (r"трет(?:ья|ьей)\s+лини[яи]", "3-я линия"),
    (r"(?:первая|1[-\s]?я)\s+лини[яи]", "1-я линия"),
    (r"(?:вторая|2[-\s]?я)\s+лини[яи]", "2-я линия"),
    (r"(?:третья|3[-\s]?я)\s+лини[яи]", "3-я линия"),
    (r"резервн(?:ая|ой)\s+(?:терапи[яи]|лини[яи])", "резервная линия"),
    (r"альтернативн(?:ая|ой)\s+(?:терапи[яи]|лини[яи])", "альтернативная линия"),
    (r"поддерживающ(?:ая|ей)\s+терапи[яи]", "поддерживающая терапия"),
]

# Treatment goal patterns
GOAL_PATTERNS = [
    (r"(?:с\s+целью|для)\s+(?:индукции\s+)?ремисси[ияи]", "ремиссия"),
    (r"профилактик[аи]", "профилактика"),
    (r"(?:симптоматическ|паллиативн)(?:ая|ой)\s+терапи[яи]", "симптоматическая терапия"),
    (r"(?:эрадикаци[яи]|элиминаци[яи])", "эрадикация"),
    (r"(?:контрол[яь]|управлени[еяю])\s+(?:симптом|заболевани)", "контроль заболевания"),
]

# Population restriction patterns
POPULATION_PATTERNS = [
    (r"дет(?:и|ей|ям|ского\s+возраста)", "дети"),
    (r"взросл(?:ые|ых|ым)", "взрослые"),
    (r"пожил(?:ые|ых|ым|ого\s+возраста)", "пожилые"),
    (r"берем(?:енн(?:ые|ых|ость|ости))", "беременные"),
    (r"корм(?:ящ(?:ие|их)|ление\s+грудью)", "кормящие"),
    (r"почечн(?:ая|ой)\s+недостаточност", "почечная недостаточность"),
    (r"печ[её]ночн(?:ая|ой)\s+недостаточност", "печёночная недостаточность"),
]


class ContextExtractor:
    def extract_from_document(self, title: str, sections: list[dict]) -> list[dict]:
        """Extract clinical contexts from a document's sections.

        Args:
            title: Document title (often contains disease name)
            sections: List of {"title": str, "fragments": [{"text": str, ...}]}

        Returns:
            List of context dicts with disease_name, line_of_therapy, treatment_goal, population, context_signature.
        """
        disease_name = self._extract_disease_from_title(title)
        contexts = []
        seen_signatures = set()

        for section in sections:
            section_text = " ".join(f.get("text", "") for f in section.get("fragments", []))
            full_text = f"{section.get('title', '')} {section_text}"

            line = self._extract_therapy_line(full_text)
            goal = self._extract_treatment_goal(full_text)
            population = self._extract_population(full_text)

            ctx = {
                "disease_name": disease_name,
                "line_of_therapy": line,
                "treatment_goal": goal,
                "population_json": {"restrictions": population} if population else None,
                "extractor_version": EXTRACTOR_VERSION,
                "confidence": 0.8,
            }
            sig = self._make_signature(ctx)
            if sig not in seen_signatures:
                seen_signatures.add(sig)
                ctx["context_signature"] = sig
                contexts.append(ctx)

        # Always return at least one base context
        if not contexts:
            ctx = {
                "disease_name": disease_name,
                "line_of_therapy": None,
                "treatment_goal": None,
                "population_json": None,
                "extractor_version": EXTRACTOR_VERSION,
                "confidence": 0.6,
            }
            ctx["context_signature"] = self._make_signature(ctx)
            contexts.append(ctx)

        return contexts

    def _extract_disease_from_title(self, title: str) -> str:
        """Extract disease name from document title."""
        # Clinical rec titles typically follow pattern: "Клинические рекомендации: <Disease>"
        # or just "<Disease>"
        title = title.strip()
        for prefix in ["Клинические рекомендации", "Клиническая рекомендация"]:
            if title.lower().startswith(prefix.lower()):
                remainder = title[len(prefix):].strip().lstrip(":").lstrip(".").strip()
                if remainder:
                    return remainder
        return title

    def _extract_therapy_line(self, text: str) -> str | None:
        for pattern, label in LINE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    def _extract_treatment_goal(self, text: str) -> str | None:
        for pattern, label in GOAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return label
        return None

    def _extract_population(self, text: str) -> list[str]:
        found = []
        for pattern, label in POPULATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(label)
        return found

    def _make_signature(self, ctx: dict) -> str:
        raw = f"{ctx['disease_name']}|{ctx.get('line_of_therapy', '')}|{ctx.get('treatment_goal', '')}|{ctx.get('population_json', '')}"
        return hashlib.md5(raw.encode()).hexdigest()

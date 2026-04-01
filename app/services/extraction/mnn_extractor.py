"""MNN (INN) extractor — finds and canonicalizes international nonproprietary names in text fragments."""

import logging
import re

from app.core.sync_database import get_sync_session
from app.models.molecule import Molecule, MoleculeSynonym

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "mnn_v1.0"


class MnnExtractor:
    def __init__(self):
        self._molecules: list[dict] = []
        self._pattern: re.Pattern | None = None
        self._loaded = False

    def load_dictionary(self) -> None:
        """Load MNN dictionary from DB."""
        session = get_sync_session()
        try:
            molecules = session.query(Molecule).all()
            self._molecules = []
            all_terms: list[tuple[str, int]] = []

            for mol in molecules:
                mol_dict = {"id": mol.id, "inn_ru": mol.inn_ru, "inn_en": mol.inn_en}
                self._molecules.append(mol_dict)
                all_terms.append((re.escape(mol.inn_ru.lower()), mol.id))
                if mol.inn_en:
                    all_terms.append((re.escape(mol.inn_en.lower()), mol.id))

            synonyms = session.query(MoleculeSynonym).all()
            for syn in synonyms:
                all_terms.append((re.escape(syn.synonym_text.lower()), syn.molecule_id))

            if all_terms:
                # Sort by length descending so longer matches take priority
                all_terms.sort(key=lambda x: len(x[0]), reverse=True)
                pattern_str = "|".join(f"(?P<m{i}>{term})" for i, (term, _) in enumerate(all_terms))
                self._pattern = re.compile(pattern_str, re.IGNORECASE)
                self._term_to_mol = {f"m{i}": mol_id for i, (_, mol_id) in enumerate(all_terms)}
            else:
                self._pattern = None
                self._term_to_mol = {}

            self._loaded = True
            logger.info("Loaded MNN dictionary: %d molecules, %d terms", len(molecules), len(all_terms))
        finally:
            session.close()

    def extract(self, text: str) -> list[dict]:
        """Extract MNN mentions from text.

        Returns list of {"molecule_id": int, "inn_ru": str, "span": (start, end), "confidence": float}
        """
        if not self._loaded:
            self.load_dictionary()

        if not self._pattern:
            return []

        results = []
        seen_ids = set()

        for match in self._pattern.finditer(text):
            group_name = match.lastgroup
            if group_name and group_name in self._term_to_mol:
                mol_id = self._term_to_mol[group_name]
                if mol_id not in seen_ids:
                    seen_ids.add(mol_id)
                    mol_dict = next((m for m in self._molecules if m["id"] == mol_id), None)
                    results.append({
                        "molecule_id": mol_id,
                        "inn_ru": mol_dict["inn_ru"] if mol_dict else "",
                        "span": (match.start(), match.end()),
                        "matched_text": match.group(),
                        "confidence": 0.9,
                        "extractor_version": EXTRACTOR_VERSION,
                    })

        return results

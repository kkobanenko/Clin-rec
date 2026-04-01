"""Tests for MNN extractor."""

import re
from unittest.mock import MagicMock, patch

from app.services.extraction.mnn_extractor import MnnExtractor


def _make_extractor(molecules: dict) -> MnnExtractor:
    """Create a pre-loaded MnnExtractor with given molecules (inn_ru -> id)."""
    extractor = MnnExtractor.__new__(MnnExtractor)
    extractor._loaded = True
    extractor._molecules = [{"id": mid, "inn_ru": inn, "inn_en": None} for inn, mid in molecules.items()]

    if molecules:
        terms = [(re.escape(inn.lower()), mid) for inn, mid in molecules.items()]
        terms.sort(key=lambda x: len(x[0]), reverse=True)
        pattern_str = "|".join(f"(?P<m{i}>{term})" for i, (term, _) in enumerate(terms))
        extractor._pattern = re.compile(pattern_str, re.IGNORECASE)
        extractor._term_to_mol = {f"m{i}": mid for i, (_, mid) in enumerate(terms)}
    else:
        extractor._pattern = None
        extractor._term_to_mol = {}

    return extractor


class TestMnnExtractor:
    def test_init(self):
        """MnnExtractor initializes with _loaded=False."""
        extractor = MnnExtractor()
        assert extractor._loaded is False

    def test_extract_no_patterns(self):
        """Returns empty list when no patterns loaded."""
        extractor = _make_extractor({})
        result = extractor.extract("Метотрексат 10 мг в неделю")
        assert result == []

    def test_extract_finds_molecules(self):
        """Finds known molecules in text."""
        extractor = _make_extractor({"метотрексат": 1})
        result = extractor.extract("Метотрексат 10 мг в неделю")
        assert len(result) == 1
        assert result[0]["molecule_id"] == 1

    def test_extract_multiple_molecules(self):
        """Finds multiple molecules in text."""
        extractor = _make_extractor({"метотрексат": 1, "лефлуномид": 2})
        result = extractor.extract("Метотрексат или лефлуномид")
        assert len(result) == 2

    def test_extract_deduplicates(self):
        """Same molecule mentioned twice produces one result."""
        extractor = _make_extractor({"метотрексат": 1})
        result = extractor.extract("Метотрексат 10 мг, затем метотрексат 15 мг")
        assert len(result) == 1

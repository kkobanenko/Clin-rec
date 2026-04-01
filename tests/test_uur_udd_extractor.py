"""Tests for UUR/UDD extractor."""

from app.services.extraction.uur_udd_extractor import UurUddExtractor


class TestUurUddExtractor:
    def setup_method(self):
        self.extractor = UurUddExtractor()

    def test_extract_uur_a(self):
        result = self.extractor.extract("Уровень убедительности рекомендаций A")
        assert len(result) == 1
        assert result[0]["uur"] == "A"

    def test_extract_udd_1(self):
        result = self.extractor.extract("Уровень достоверности доказательств 1")
        assert len(result) == 1
        assert result[0]["udd"] == "1"

    def test_extract_combined(self):
        result = self.extractor.extract("УУР A, УДД 1")
        assert len(result) == 1
        assert result[0]["uur"] == "A"
        assert result[0]["udd"] == "1"

    def test_extract_no_match(self):
        result = self.extractor.extract("Обычный текст без классификации")
        assert result == []

    def test_extract_uur_b(self):
        result = self.extractor.extract("Уровень убедительности рекомендаций B")
        assert len(result) == 1
        assert result[0]["uur"] == "B"

    def test_extract_udd_2(self):
        result = self.extractor.extract("Уровень достоверности доказательств 2")
        assert len(result) == 1
        assert result[0]["udd"] == "2"

    def test_cyrillic_uur_normalized(self):
        result = self.extractor.extract("УУР А, УДД 1")  # Cyrillic А
        assert len(result) == 1
        assert result[0]["uur"] == "A"  # Normalized to Latin A

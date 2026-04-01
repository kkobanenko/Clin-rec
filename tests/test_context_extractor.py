"""Tests for context extractor."""

from app.services.extraction.context_extractor import ContextExtractor


class TestContextExtractor:
    def setup_method(self):
        self.extractor = ContextExtractor()

    def test_extract_therapy_line_first(self):
        result = self.extractor._extract_therapy_line("Терапия первой линии")
        assert result == "1-я линия"

    def test_extract_therapy_line_second(self):
        result = self.extractor._extract_therapy_line("Терапия второй линии")
        assert result == "2-я линия"

    def test_extract_therapy_line_reserve(self):
        result = self.extractor._extract_therapy_line("Резервная терапия")
        assert result == "резервная линия"

    def test_extract_therapy_line_none(self):
        result = self.extractor._extract_therapy_line("Обычный текст")
        assert result is None

    def test_extract_population_children(self):
        result = self.extractor._extract_population("Дети в возрасте от 2 до 18 лет")
        assert "дети" in result

    def test_extract_population_adults(self):
        result = self.extractor._extract_population("Взрослые пациенты старше 18 лет")
        assert "взрослые" in result

    def test_extract_population_empty(self):
        result = self.extractor._extract_population("Общий текст")
        assert result == []

    def test_extract_disease_from_title(self):
        result = self.extractor._extract_disease_from_title("Ревматоидный артрит")
        assert result == "Ревматоидный артрит"

    def test_extract_disease_strips_prefix(self):
        result = self.extractor._extract_disease_from_title("Клинические рекомендации: Ревматоидный артрит")
        assert result == "Ревматоидный артрит"

    def test_context_signature(self):
        ctx = {
            "disease_name": "Ревматоидный артрит",
            "line_of_therapy": "1-я линия",
            "treatment_goal": None,
            "population_json": {"restrictions": ["взрослые"]},
        }
        sig = self.extractor._make_signature(ctx)
        assert isinstance(sig, str)
        assert len(sig) > 0

    def test_extract_from_document(self):
        title = "Ревматоидный артрит"
        sections = [{"title": "Лечение первой линии", "fragments": [{"text": "Метотрексат назначается взрослым"}]}]
        contexts = self.extractor.extract_from_document(title, sections)
        assert len(contexts) >= 1
        assert contexts[0]["disease_name"] == "Ревматоидный артрит"

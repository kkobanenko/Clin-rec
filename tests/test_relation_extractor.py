"""Tests for relation extractor."""

from app.services.extraction.relation_extractor import RelationExtractor


class TestRelationExtractor:
    def setup_method(self):
        self.extractor = RelationExtractor()

    def test_explicit_alternative(self):
        text = "В качестве альтернативы метотрексату рекомендуется лефлуномид"
        result = self.extractor.extract(text)
        assert len(result) > 0
        types = {r["relation_type"] for r in result}
        assert "explicit_alternative_same_line" in types or "same_line_option" in types

    def test_switch_intolerance(self):
        text = "При непереносимости метотрексата перевод на лефлуномид"
        result = self.extractor.extract(text)
        assert len(result) > 0

    def test_no_signal(self):
        text = "Общая информация о заболевании"
        result = self.extractor.extract(text)
        # Should return empty or no_substitution_signal
        if result:
            types = {r["relation_type"] for r in result}
            assert "no_substitution_signal" in types or len(types) == 0

    def test_classify_dominant(self):
        signals = [
            {"relation_type": "explicit_alternative_same_line", "confidence": 0.9, "signal_text": "a", "context_text": "a", "span": (0, 1), "extractor_version": "v1"},
            {"relation_type": "same_line_option", "confidence": 0.7, "signal_text": "b", "context_text": "b", "span": (0, 1), "extractor_version": "v1"},
            {"relation_type": "explicit_alternative_same_line", "confidence": 0.85, "signal_text": "c", "context_text": "c", "span": (0, 1), "extractor_version": "v1"},
        ]
        dominant, confidence = self.extractor.classify_relation(signals)
        assert dominant == "explicit_alternative_same_line"
        assert 0 < confidence <= 1.0

    def test_classify_empty(self):
        dominant, confidence = self.extractor.classify_relation([])
        assert dominant == "no_substitution_signal"

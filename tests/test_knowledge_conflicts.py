from app.services.knowledge_conflicts import _normalize_claim_text


def test_normalize_claim_text_collapses_space():
    assert _normalize_claim_text("  A  B\tc  ") == "a b c"

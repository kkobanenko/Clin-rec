from app.services.extraction.inn_heuristic import collect_parenthetical_inn_candidates


def test_collect_parenthetical_finds_metformin():
    text = "Рекомендуется метформин (metformin) в качестве первой линии."
    got = collect_parenthetical_inn_candidates(text)
    assert "Metformin" in got or "metformin" in {x.lower() for x in got}


def test_collect_insulin_glargine_two_words():
    text = "инсулин гларгин (insulin glargine) применяют"
    got = collect_parenthetical_inn_candidates(text)
    assert any("insulin" in x.lower() and "glargine" in x.lower() for x in got)


def test_collect_mnn_label_line():
    text = "Назначение препарата.\nМНН: metformin\nДозировка"
    got = collect_parenthetical_inn_candidates(text)
    assert any("metformin" in x.lower() for x in got)

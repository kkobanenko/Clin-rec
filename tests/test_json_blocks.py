from app.services.json_blocks import (
    collect_canonical_blocks,
    serialize_rules_to_text,
)


def test_collect_canonical_blocks_finds_marked_dicts() -> None:
    payload = {
        "data": {
            "items": [
                {"title": "A", "rules": [["1", "краткая", "информация"]]},
                {"name": "B", "html": "<p>x</p>"},
                {"image_ref": "img://1"},
            ]
        }
    }
    blocks = collect_canonical_blocks(payload)
    assert len(blocks) == 3
    assert blocks[0].source_path == "/data/items/0"
    assert blocks[1].content_kind == "html"
    assert blocks[2].content_kind == "image"


def test_collect_canonical_blocks_stable_block_id_without_id() -> None:
    payload = {"root": [{"title": "X", "rules": ["1", "a"]}]}
    first = collect_canonical_blocks(payload)[0].block_id
    second = collect_canonical_blocks(payload)[0].block_id
    assert first == second


def test_serialize_rules_primitives_and_lists() -> None:
    assert serialize_rules_to_text(["1", "краткая", "информация"]) == "1. краткая информация"
    assert serialize_rules_to_text(["краткая", "информация"]) == "краткая информация"
    assert serialize_rules_to_text([["1", "A"], ["2", "B"]]) == "1. A\n2. B"


def test_serialize_rules_dict_sorted_and_stable() -> None:
    text = serialize_rules_to_text({"b": "two", "a": "one"})
    assert text.splitlines() == ["a: one", "b: two"]
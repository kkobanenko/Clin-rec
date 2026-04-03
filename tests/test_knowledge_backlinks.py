from app.services.knowledge_backlinks import collect_slug_candidates_from_markdown


def test_collect_wiki_slugs():
    wiki, md = collect_slug_candidates_from_markdown("См. [[digest/v1]] и [[master_index]].")
    assert wiki == {"digest/v1", "master_index"}
    assert md == set()


def test_collect_ignores_external_urls():
    wiki, md = collect_slug_candidates_from_markdown("[a](https://x/y) [[internal/slug]]")
    assert wiki == {"internal/slug"}
    assert md == set()

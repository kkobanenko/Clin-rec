from types import SimpleNamespace

from app.services.normalize import NormalizeService


def test_normalize_json_produces_source_block_traceability() -> None:
    service = NormalizeService()
    sections = service._normalize_json(b'{"title":"Section A","rules":["1","k","i"]}')
    assert sections
    assert sections[0].source_block_id is not None
    assert sections[0].fragments
    assert sections[0].fragments[0].source_block_id == sections[0].source_block_id
    assert sections[0].fragments[0].content_kind == "text"


def test_extract_sections_detailed_marks_json_source(monkeypatch):
    service = NormalizeService()
    version = SimpleNamespace(id=42, source_type_primary="html+pdf")
    json_artifact = SimpleNamespace(id=99, raw_path="json")

    monkeypatch.setattr(
        "app.services.normalize.download_artifact",
        lambda _path: b'{"title":"S","rules":["k","i"]}',
    )

    result = service._extract_sections_detailed(version, json_artifact, None, None)
    assert result.source_artifact_id == 99
    assert result.source_artifact_type == "json"
    assert result.sections
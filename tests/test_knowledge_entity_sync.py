"""Юнит-тесты синхронизации molecule → entity_registry."""

from unittest.mock import MagicMock

from app.services.knowledge_entity_sync import ensure_molecule_entities


def test_ensure_molecule_entities_returns_zero_for_empty_ids():
    session = MagicMock()
    assert ensure_molecule_entities(session, []) == 0
    session.add.assert_not_called()


def test_ensure_molecule_entities_skips_when_molecule_missing():
    session = MagicMock()
    exec_ret = MagicMock()
    exec_ret.scalars.return_value.all.return_value = []
    session.execute.return_value = exec_ret
    session.get.return_value = None  # molecule not in DB

    n = ensure_molecule_entities(session, [99])
    assert n == 0
    session.add.assert_not_called()

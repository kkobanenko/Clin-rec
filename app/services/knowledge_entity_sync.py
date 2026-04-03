"""
Синхронизация clinical extraction → entity_registry (TZ): молекулы как сущности KB.

После извлечения МНН из фрагментов создаём/находим записи entity_type=molecule с привязкой к molecule.id.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from sqlalchemy import select

from app.models.knowledge import EntityRegistry
from app.models.molecule import Molecule

logger = logging.getLogger(__name__)

SYNC_VERSION = "molecule_entity_v1"


def ensure_molecule_entities(session, molecule_ids: Iterable[int]) -> int:
    """
    Для каждого molecule_id из извлечения: если ещё нет EntityRegistry с external_refs_json.molecule_id,
    создаём строку (canonical_name = inn_ru).

    Возвращает число новых записей (ещё не flush/commit).
    """
    ids = {int(x) for x in molecule_ids if x is not None}
    if not ids:
        return 0

    existing: set[int] = set()
    for row in session.execute(select(EntityRegistry).where(EntityRegistry.entity_type == "molecule")).scalars().all():
        refs = row.external_refs_json or {}
        mid = refs.get("molecule_id")
        if mid is not None:
            existing.add(int(mid))

    created = 0
    for mid in sorted(ids):
        if mid in existing:
            continue
        mol = session.get(Molecule, mid)
        if not mol:
            logger.warning("ensure_molecule_entities: molecule id=%s not in DB, skip", mid)
            continue
        ent = EntityRegistry(
            entity_type="molecule",
            canonical_name=(mol.inn_ru or f"molecule-{mid}")[:500],
            external_refs_json={"molecule_id": mid, "sync": SYNC_VERSION},
            aliases_json={"inn_en": mol.inn_en} if mol.inn_en else {"source": "mnn_pipeline"},
            status="active",
        )
        session.add(ent)
        existing.add(mid)
        created += 1

    if created:
        logger.info("ensure_molecule_entities: created %d new entity_registry rows", created)
    return created

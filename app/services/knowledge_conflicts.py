"""
Минимальное выявление конфликтов по claims (TZ §13): несколько fact с разным текстом в одном артефакте.
Без ML; нормализация текста — lower + схлопывание пробелов.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select

from app.core.sync_database import get_sync_session
from app.models.knowledge import KnowledgeClaim

logger = logging.getLogger(__name__)


def _normalize_claim_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def detect_conflicts_sync() -> dict[str, Any]:
    """
    Для каждого artifact_id собираем claim_type=fact.
    Если есть ≥2 различных нормализованных claim_text — всем этим claims ставим один conflict_group_id.
    Уже помеченные группы перезаписываем при новом прогоне только для затронутых артефактов.
    """
    session = get_sync_session()
    try:
        claims = session.execute(
            select(KnowledgeClaim).where(KnowledgeClaim.claim_type == "fact")
        ).scalars().all()

        by_artifact: dict[int, list[KnowledgeClaim]] = {}
        for c in claims:
            by_artifact.setdefault(c.artifact_id, []).append(c)

        max_gid = session.scalar(select(func.max(KnowledgeClaim.conflict_group_id))) or 0
        next_gid = int(max_gid) + 1
        groups_created = 0
        claims_tagged = 0

        for _aid, lst in by_artifact.items():
            if len(lst) < 2:
                continue
            distinct_norm: set[str] = set()
            for c in lst:
                distinct_norm.add(_normalize_claim_text(c.claim_text))
            if len(distinct_norm) < 2:
                continue

            gid = next_gid
            next_gid += 1
            groups_created += 1
            for c in lst:
                c.conflict_group_id = gid
                c.is_conflicted = True
                claims_tagged += 1

        session.commit()
        out = {
            "status": "ok",
            "conflict_groups_created": groups_created,
            "claims_tagged": claims_tagged,
        }
        logger.info("detect_conflicts: %s", out)
        return out
    except Exception:
        session.rollback()
        logger.exception("detect_conflicts_sync failed")
        raise
    finally:
        session.close()

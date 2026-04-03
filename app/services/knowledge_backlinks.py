"""
Пересчёт artifact_backlink из разметки content_md (TZ §12.2).

Ищем:
- wiki-ссылки [[canonical_slug]]
- markdown-ссылки [лейбл](canonical_slug) если цель не похожа на URL.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import delete, select

from app.core.sync_database import get_sync_session
from app.models.knowledge import ArtifactBacklink, KnowledgeArtifact

logger = logging.getLogger(__name__)

WIKI_LINK = re.compile(r"\[\[([^\]]+?)\]\]")
# Цель в круглых скобках; пропускаем http(s) и строки с пробелами (не slug).
MD_LINK = re.compile(r"\[[^\]]*\]\(\s*([^)]+?)\s*\)")


def collect_slug_candidates_from_markdown(text: str) -> tuple[set[str], set[str]]:
    """Возвращает (slug из wiki, slug из markdown) для последующего матчинга по canonical_slug."""
    wiki = {s.strip() for s in WIKI_LINK.findall(text or "")}
    md_targets: set[str] = set()
    for raw in MD_LINK.findall(text or ""):
        t = raw.strip()
        if not t or " " in t or t.startswith("http://") or t.startswith("https://"):
            continue
        md_targets.add(t)
    return wiki, md_targets


def refresh_all_backlinks_sync() -> dict[str, Any]:
    """
    Идемпотентно: удаляем старые рёбра link_type parsed_wiki/parsed_md с каждого артефакта
    и заново строим по текущему content_md.
    """
    session = get_sync_session()
    inserted = 0
    deleted = 0
    try:
        rows = session.execute(select(KnowledgeArtifact.canonical_slug, KnowledgeArtifact.id)).all()
        slug_to_id: dict[str, int] = {str(r[0]): int(r[1]) for r in rows}

        arts = session.execute(
            select(KnowledgeArtifact.id, KnowledgeArtifact.content_md).where(
                KnowledgeArtifact.content_md.isnot(None)
            )
        ).all()

        link_types = ("parsed_wiki", "parsed_md")

        for from_id, content_md in arts:
            if not content_md:
                continue
            res = session.execute(
                delete(ArtifactBacklink).where(
                    ArtifactBacklink.from_artifact_id == from_id,
                    ArtifactBacklink.link_type.in_(link_types),
                )
            )
            deleted += int(res.rowcount or 0)

            wiki_slugs, md_slugs = collect_slug_candidates_from_markdown(str(content_md))
            # Одна пара (from,to) — одно ребро: тип wiki приоритетнее markdown.
            targets_done: set[int] = set()

            for slug in sorted(wiki_slugs):
                to_id = slug_to_id.get(slug)
                if to_id is None or to_id == from_id or to_id in targets_done:
                    continue
                targets_done.add(to_id)
                session.add(
                    ArtifactBacklink(
                        from_artifact_id=from_id,
                        to_artifact_id=to_id,
                        link_type="parsed_wiki",
                    )
                )
                inserted += 1

            for slug in sorted(md_slugs):
                to_id = slug_to_id.get(slug)
                if to_id is None or to_id == from_id or to_id in targets_done:
                    continue
                targets_done.add(to_id)
                session.add(
                    ArtifactBacklink(
                        from_artifact_id=from_id,
                        to_artifact_id=to_id,
                        link_type="parsed_md",
                    )
                )
                inserted += 1

        session.commit()
        out = {
            "status": "ok",
            "artifacts_with_content": len(arts),
            "backlinks_inserted": inserted,
            "backlink_rows_removed": deleted,
        }
        logger.info("refresh backlinks: %s", out)
        return out
    except Exception:
        session.rollback()
        logger.exception("refresh_all_backlinks_sync failed")
        raise
    finally:
        session.close()

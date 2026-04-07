"""
Эвристическое обнаружение МНН в тексте КР, если их ещё нет в справочнике molecule.

Клинические рекомендации часто дают международное название в скобках после русского:
  «метформин (metformin)», «инсулин гларгин (insulin glargine)».

Базовый MnnExtractor сопоставляет только с уже загруженными строками в БД — без
расширения словаря новые молекулы не появляются. Этот модуль извлекает кандидатов
из скобок и создаёт записи Molecule (и при необходимости перезагружает словарь).
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Латинское название в круглых скобках (ASCII и типичные Unicode-варианты).
_PAREN_LATIN = re.compile(
    r"[\(（]\s*([A-Za-z][A-Za-z0-9]+(?:\s+[A-Za-z][A-Za-z0-9]+){0,3})\s*[\)）]"
)

# Строка вида «МНН: metformin» / «INN — insulin glargine» (в КР латиница часто без скобок).
_MNN_LABEL_LATIN = re.compile(
    r"(?:^|[\s;,:])(?:МНН|мнн|INN|inn)\s*[:;—\-–]?\s*([A-Za-z][a-z0-9]*(?:\s+[a-z][a-z0-9]*){0,3})(?=[\s\.,;:\)\]»\"]|$)",
    re.MULTILINE,
)

# Слишком короткие / явно не ЛП
_STOP = frozenset({
    "and",
    "or",
    "the",
    "for",
    "with",
    "from",
    "type",
    "year",
    "day",
    "per",
    "mg",
    "ml",
    "kg",
    "hr",
    "vs",
    "see",
    "note",
    "table",
    "figure",
    "group",
    "level",
    "risk",
    "high",
    "low",
    "long",
    "term",
    "use",
    "not",
    "may",
    "can",
    "one",
    "two",
    "new",
    "old",
    "according",
    "based",
    "using",
    "other",
    "first",
    "second",
    "third",
    "study",
    "trial",
    "trials",
    "patient",
    "patients",
    "adult",
    "adults",
    "child",
    "children",
    "clinical",
    "should",
    "could",
    "would",
    "there",
    "their",
    "which",
    "these",
    "those",
    "such",
    "also",
    "only",
    "both",
    "each",
    "most",
    "some",
})


def _normalize_inn_token(raw: str) -> str | None:
    s = raw.strip()
    if len(s) < 4:
        return None
    parts = s.lower().split()
    if any(p in _STOP for p in parts):
        return None
    # Одно слово: минимум 5 букв (отсекает "acid", "test" частично)
    if len(parts) == 1 and len(parts[0]) < 5:
        return None
    return s.title() if s.islower() or s.isupper() else s


def collect_parenthetical_inn_candidates(text: str) -> set[str]:
    """Возвращает уникальные строки-кандидаты МНН из текста фрагмента."""
    out: set[str] = set()
    raw = text or ""
    for m in _PAREN_LATIN.finditer(raw):
        token = _normalize_inn_token(m.group(1))
        if token:
            out.add(token)
    for m in _MNN_LABEL_LATIN.finditer(raw):
        token = _normalize_inn_token(m.group(1))
        if token:
            out.add(token)
    return out


def collect_all_inn_candidates_for_texts(texts: list[str]) -> set[str]:
    """Объединение кандидатов по списку фрагментов (один проход на версию документа)."""
    merged: set[str] = set()
    for t in texts:
        merged |= collect_parenthetical_inn_candidates(t)
    return merged


def ensure_molecules_for_inn_strings(session: Session, candidates: set[str]) -> int:
    """
    Для каждого кандидата: если нет molecule с таким inn_ru (без учёта регистра) — создаём строку.

    inn_ru хранит канонический вид (как в тексте после нормализации); inn_en дублирует для латиницы.
    Возвращает число вставленных строк.
    """
    from sqlalchemy import func

    from app.models.molecule import Molecule

    if not candidates:
        return 0

    inserted = 0
    for cand in sorted(candidates):
        canonical = cand.strip()
        if not canonical:
            continue
        exists = (
            session.query(Molecule.id)
            .filter(func.lower(Molecule.inn_ru) == canonical.lower())
            .first()
        )
        if exists:
            continue
        session.add(
            Molecule(
                inn_ru=canonical,
                inn_en=canonical,
                atc_code=None,
            )
        )
        inserted += 1
        logger.info("inn_heuristic: new molecule from text: %s", canonical)

    if inserted:
        session.flush()
    return inserted

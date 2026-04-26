"""Canonical JSON block extraction for JSON-first normalization."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class CanonicalJsonBlock:
    block_id: str
    source_path: str
    order: int
    title: str | None
    rules: Any | None
    content_kind: str
    html: str | None
    image_ref: str | None
    table: Any | None
    raw: dict


def _pointer(path_parts: list[str]) -> str:
    if not path_parts:
        return "/"
    escaped = [part.replace("~", "~0").replace("/", "~1") for part in path_parts]
    return "/" + "/".join(escaped)


def _first_present(data: dict, keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _to_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _block_id(raw: dict, source_path: str) -> str:
    existing = _first_present(raw, ("id", "Id", "ID", "code", "Code", "path", "Path"))
    if existing is not None and str(existing).strip():
        return str(existing)
    normalized_raw = json.dumps(raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(f"{source_path}:{normalized_raw}".encode("utf-8")).hexdigest()


def route_block_kind(block: CanonicalJsonBlock) -> str:
    if block.image_ref:
        return "image"
    if block.html:
        return "html"
    if block.table is not None:
        return "table_like"
    if block.title or block.rules is not None:
        return "text"
    return "unknown"


def collect_canonical_blocks(payload: dict | list) -> list[CanonicalJsonBlock]:
    blocks: list[CanonicalJsonBlock] = []
    block_markers = {
        "title",
        "Title",
        "name",
        "Name",
        "rules",
        "Rules",
        "html",
        "HTML",
        "image",
        "image_ref",
        "img",
        "table",
    }

    def walk(node: Any, path_parts: list[str]) -> None:
        if isinstance(node, dict):
            if any(marker in node for marker in block_markers):
                source_path = _pointer(path_parts)
                block = CanonicalJsonBlock(
                    block_id=_block_id(node, source_path),
                    source_path=source_path,
                    order=len(blocks),
                    title=_to_string(_first_present(node, ("title", "Title", "name", "Name"))),
                    rules=_first_present(node, ("rules", "Rules")),
                    content_kind="unknown",
                    html=_to_string(_first_present(node, ("html", "HTML"))),
                    image_ref=_to_string(_first_present(node, ("image_ref", "image", "img"))),
                    table=node.get("table"),
                    raw=node,
                )
                blocks.append(block)

            for key, value in node.items():
                walk(value, [*path_parts, str(key)])
        elif isinstance(node, list):
            for idx, item in enumerate(node):
                walk(item, [*path_parts, str(idx)])

    walk(payload, [])
    return [
        CanonicalJsonBlock(
            block_id=block.block_id,
            source_path=block.source_path,
            order=block.order,
            title=block.title,
            rules=block.rules,
            content_kind=route_block_kind(block),
            html=block.html,
            image_ref=block.image_ref,
            table=block.table,
            raw=block.raw,
        )
        for block in blocks
    ]


def serialize_rules_to_text(rules: Any) -> str:
    if rules is None:
        return ""
    if isinstance(rules, str):
        return rules.strip()
    if isinstance(rules, (int, float, bool)):
        return str(rules)
    if isinstance(rules, dict):
        lines: list[str] = []
        for key in sorted(rules):
            value_text = serialize_rules_to_text(rules[key])
            lines.append(f"{key}: {value_text}" if value_text else f"{key}:")
        return "\n".join(line for line in lines if line.strip())
    if isinstance(rules, list):
        if not rules:
            return ""
        if all(not isinstance(item, (list, dict)) for item in rules):
            parts = [str(item).strip() for item in rules if str(item).strip()]
            if not parts:
                return ""
            if len(parts) >= 2 and parts[0].isdigit():
                return f"{parts[0]}. {' '.join(parts[1:])}"
            return " ".join(parts)

        lines: list[str] = []
        for item in rules:
            line = serialize_rules_to_text(item).strip()
            if line:
                lines.append(line)
        return "\n".join(lines)
    return str(rules).strip()
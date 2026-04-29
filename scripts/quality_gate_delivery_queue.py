"""File-backed delivery queue for quality gate notifications."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def ensure_spool_dir(spool_dir: str | Path) -> Path:
    path = Path(spool_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def enqueue_payload(spool_dir: str | Path, payload: dict[str, Any]) -> Path:
    path = ensure_spool_dir(spool_dir)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = path / f"{stamp}_{uuid4().hex}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def list_queue_files(spool_dir: str | Path) -> list[Path]:
    path = Path(spool_dir)
    if not path.exists():
        return []
    return sorted([item for item in path.iterdir() if item.is_file() and item.suffix == ".json"])


def load_payload(file_path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Queue file is not a JSON object: {file_path}")
    return payload


def remove_payload(file_path: str | Path) -> None:
    path = Path(file_path)
    if path.exists():
        path.unlink()

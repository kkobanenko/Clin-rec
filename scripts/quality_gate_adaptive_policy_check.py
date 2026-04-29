#!/usr/bin/env python3
"""CLI checker for adaptive policy recommendations."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check adaptive policy recommendations")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--queue-size-warn", type=float, default=20.0)
    parser.add_argument("--queue-size-fail", type=float, default=100.0)
    parser.add_argument("--baseline-window", type=int, default=10)
    parser.add_argument("--spool-dir", default=os.getenv("QUALITY_GATE_NOTIFY_SPOOL_DIR", ".artifacts/quality_gate_notify_queue"))
    parser.add_argument("--registry-dir", default=os.getenv("QUALITY_GATE_INCIDENT_REGISTRY_DIR", ".artifacts/quality_gate_incident_registry"))
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--fail-on-mode", default="none", choices=["none", "tighten"])
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    return parser


def _fetch_report(*, api_base: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    response = httpx.get(
        f"{api_base.rstrip('/')}/outputs/quality-gate/adaptive-policy",
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("adaptive-policy endpoint returned non-object payload")
    return payload


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    params = {
        "max_versions": args.max_versions,
        "high_skip_threshold": args.high_skip_threshold,
        "max_avg_skip_rate": args.max_avg_skip_rate,
        "min_candidate_pairs": args.min_candidate_pairs,
        "queue_size_warn": args.queue_size_warn,
        "queue_size_fail": args.queue_size_fail,
        "baseline_window": args.baseline_window,
        "spool_dir": args.spool_dir,
        "registry_dir": args.registry_dir,
        "max_items": args.max_items,
    }

    try:
        payload = _fetch_report(api_base=args.api_base, params=params, timeout=args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"adaptive-policy check: API request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    mode = str(payload.get("mode") or "unknown")
    print(f"adaptive-policy check: mode={mode} recommendations={len(payload.get('recommendations') or [])}")

    if args.fail_on_mode == "tighten" and mode == "tighten":
        print("adaptive-policy check: FAILED (tighten mode triggered)", file=sys.stderr)
        return 1

    print("adaptive-policy check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

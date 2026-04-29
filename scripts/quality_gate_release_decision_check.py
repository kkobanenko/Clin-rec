#!/usr/bin/env python3
"""CLI checker for release decision endpoint."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import httpx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check release decision")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--min-score", type=float, default=60.0)
    parser.add_argument("--max-allowed-ratio-delta", type=float, default=0.15)
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
    parser.add_argument("--fail-on-decision", default="block", choices=["block", "review", "none"])
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--json", action="store_true")
    return parser


def _fetch_report(*, api_base: str, params: dict[str, Any], timeout: float) -> dict[str, Any]:
    response = httpx.get(
        f"{api_base.rstrip('/')}/outputs/quality-gate/release-decision",
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("release-decision endpoint returned non-object payload")
    return payload


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    params = {
        "min_score": args.min_score,
        "max_allowed_ratio_delta": args.max_allowed_ratio_delta,
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
        print(f"release-decision check: API request failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    decision = str(payload.get("decision") or "unknown")
    print(f"release-decision check: decision={decision} confidence={payload.get('confidence')}")

    if args.fail_on_decision == "block" and decision == "block":
        print("release-decision check: FAILED (block)", file=sys.stderr)
        return 1
    if args.fail_on_decision == "review" and decision in {"block", "review"}:
        print("release-decision check: FAILED (review-or-block)", file=sys.stderr)
        return 1

    print("release-decision check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

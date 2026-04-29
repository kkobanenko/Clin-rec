#!/usr/bin/env python3
"""CLI checker for quality gate queue policy verdict."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import httpx


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check quality gate queue policy verdict")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--spool-dir", default="")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--fail-on-degraded", action="store_true")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def _fetch_report(*, api_base: str, max_items: int, spool_dir: str, timeout: float) -> dict[str, Any]:
    params: dict[str, Any] = {"max_items": max_items}
    if spool_dir.strip():
        params["spool_dir"] = spool_dir.strip()
    response = httpx.get(f"{api_base.rstrip('/')}/outputs/quality-gate/queue-policy", params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("queue policy endpoint returned non-object payload")
    return payload


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        report = _fetch_report(
            api_base=args.api_base,
            max_items=args.max_items,
            spool_dir=args.spool_dir,
            timeout=args.timeout,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"queue-policy check: API request failed: {exc}", file=sys.stderr)
        return 2

    verdict = str(report.get("verdict") or "unknown")
    summary = str(report.get("summary") or "")
    rules = report.get("rules") if isinstance(report.get("rules"), list) else []

    print(f"queue-policy verdict: {verdict}")
    if summary:
        print(f"summary: {summary}")
    for rule in rules:
        if isinstance(rule, dict):
            print(
                "- {name}: status={status} value={value} warn={warn} fail={fail}".format(
                    name=rule.get("name", "unknown"),
                    status=rule.get("status", "unknown"),
                    value=rule.get("value"),
                    warn=rule.get("warn_threshold"),
                    fail=rule.get("fail_threshold"),
                )
            )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if verdict == "critical":
        print("queue-policy check: FAILED", file=sys.stderr)
        return 1
    if verdict == "degraded" and args.fail_on_degraded:
        print("queue-policy check: FAILED (degraded)", file=sys.stderr)
        return 1
    if verdict == "empty" and not args.allow_empty:
        print("queue-policy check: FAILED (empty queue not allowed by policy)", file=sys.stderr)
        return 1
    if verdict == "unknown":
        print("queue-policy check: FAILED (unknown verdict)", file=sys.stderr)
        return 1

    print("queue-policy check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

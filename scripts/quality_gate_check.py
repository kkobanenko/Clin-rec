#!/usr/bin/env python3
"""Release quality gate checker.

Fetches `/outputs/quality-gate` from runtime API and enforces a configurable
policy for CI/release scripts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class GatePolicy:
    """Policy for converting gate verdict into process exit code."""

    fail_on_warn: bool = False
    fail_on_no_data: bool = True


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check automated quality gate verdict")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="Runtime API base URL")
    parser.add_argument("--max-versions", type=int, default=100)
    parser.add_argument("--high-skip-threshold", type=float, default=0.8)
    parser.add_argument("--max-avg-skip-rate", type=float, default=0.75)
    parser.add_argument("--min-candidate-pairs", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--fail-on-warn", action="store_true")
    parser.add_argument(
        "--allow-no-data",
        action="store_true",
        help="Do not fail when verdict is no-data",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON gate report for artifact logging",
    )
    return parser


def _request_report(
    *,
    api_base: str,
    max_versions: int,
    high_skip_threshold: float,
    max_avg_skip_rate: float,
    min_candidate_pairs: int,
    timeout: float,
) -> dict[str, Any]:
    params = {
        "max_versions": max_versions,
        "high_skip_threshold": high_skip_threshold,
        "max_avg_skip_rate": max_avg_skip_rate,
        "min_candidate_pairs": min_candidate_pairs,
    }
    url = f"{api_base.rstrip('/')}/outputs/quality-gate"
    response = httpx.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Quality gate endpoint returned non-object payload")
    return payload


def _format_rule_line(rule: dict[str, Any]) -> str:
    return (
        f"- {rule.get('name', 'unknown')}: status={rule.get('status', 'unknown')} "
        f"value={rule.get('value')} {rule.get('comparator', '?')} {rule.get('threshold')}"
    )


def _should_fail(verdict: str, policy: GatePolicy) -> bool:
    if verdict == "fail":
        return True
    if verdict == "warn" and policy.fail_on_warn:
        return True
    if verdict == "no-data" and policy.fail_on_no_data:
        return True
    if verdict == "unknown":
        return True
    return False


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    policy = GatePolicy(
        fail_on_warn=args.fail_on_warn,
        fail_on_no_data=not args.allow_no_data,
    )

    try:
        report = _request_report(
            api_base=args.api_base,
            max_versions=args.max_versions,
            high_skip_threshold=args.high_skip_threshold,
            max_avg_skip_rate=args.max_avg_skip_rate,
            min_candidate_pairs=args.min_candidate_pairs,
            timeout=args.timeout,
        )
    except httpx.HTTPError as exc:
        print(f"quality-gate: API request failed: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"quality-gate: unexpected error: {exc}", file=sys.stderr)
        return 2

    verdict = str(report.get("verdict") or "unknown")
    summary = str(report.get("summary") or "")
    rules = report.get("rules") or []

    print(f"quality-gate verdict: {verdict}")
    if summary:
        print(f"summary: {summary}")
    if isinstance(rules, list):
        for raw_rule in rules:
            if isinstance(raw_rule, dict):
                print(_format_rule_line(raw_rule))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if _should_fail(verdict, policy):
        print("quality-gate policy: FAILED", file=sys.stderr)
        return 1

    print("quality-gate policy: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
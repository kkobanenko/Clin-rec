#!/usr/bin/env python3
"""CLI checker for governance evidence digest calculations."""

from __future__ import annotations

import argparse
import json
import sys

from app.services.governance_evidence_digest import GovernanceEvidenceDigestService


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build governance evidence digest")
    parser.add_argument("--input-json", required=True, help="Path to JSON array with digest entries")
    parser.add_argument("--min-score", type=float, default=60.0)
    parser.add_argument("--json", action="store_true")
    return parser


def run(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        payload = json.loads(open(args.input_json, "r", encoding="utf-8").read())
    except Exception as exc:  # noqa: BLE001
        print(f"digest-check: cannot load input: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, list):
        print("digest-check: input payload must be a JSON array", file=sys.stderr)
        return 2

    service = GovernanceEvidenceDigestService()
    report = service.build_digest(payload)
    data = report.to_dict()

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))

    print(
        "digest-check: "
        f"verdict={data.get('verdict')} normalized_score={data.get('normalized_score')}"
    )

    if float(data.get("normalized_score") or 0.0) < args.min_score:
        print("digest-check: FAILED (score below threshold)", file=sys.stderr)
        return 1

    print("digest-check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

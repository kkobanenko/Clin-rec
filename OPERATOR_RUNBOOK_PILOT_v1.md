# Operator Runbook — Pilot v1

Дата: 2026-04-24

## 1. Start runtime

```bash
docker compose up -d --build
```

Check:

```bash
docker compose ps
curl -f http://localhost:8000/health
```

Open:

- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- UI: `http://localhost:8501`
- MinIO API: `http://localhost:9010`
- MinIO console: `http://localhost:9011`

## 2. Preflight

Before release/pilot decision:

```bash
bash scripts/pilot_preflight.sh
```

If script does not exist yet, manually check:

- API health;
- Postgres reachable;
- Redis reachable;
- MinIO reachable;
- bucket exists;
- migrations applied;
- free disk space;
- env vars loaded.

## 3. Run sync

Use API/UI:

```bash
curl -X POST http://localhost:8000/sync/full
```

Then poll:

```bash
curl http://localhost:8000/pipeline/runs/<run_id>
```

Check:

- status terminal: `completed` or explicit failure;
- discovered_count;
- stats_json.discovery_strategy_report;
- fallback_reason if fallback used.

## 4. Validate documents

```bash
curl http://localhost:8000/documents?page=1
curl http://localhost:8000/documents/<id>/content
curl http://localhost:8000/documents/<id>/fragments
curl http://localhost:8000/documents/<id>/artifacts
```

Check:

- content not empty;
- fragments not empty;
- artifacts valid for current version;
- fake PDF/SPA shell not treated as valid primary artifact.

## 5. Validate matrix/evidence

```bash
curl http://localhost:8000/matrix/pair-evidence
curl 'http://localhost:8000/matrix/cell?from_molecule_id=<id>&to_molecule_id=<id>&model_version_id=<id>'
```

Check:

- pair evidence exists;
- matrix cell has score/confidence;
- supporting evidence is visible.

## 6. Generate memo/output

If API auth is enabled, include header:

```bash
-H 'X-CRIN-API-Key: <key>'
```

```bash
curl -X POST http://localhost:8000/outputs/memo \
  -H 'Content-Type: application/json' \
  -d '{"title":"pilot memo"}'
```

Poll task:

```bash
curl http://localhost:8000/tasks/<task_id>
```

Open output:

```bash
curl http://localhost:8000/outputs/<output_id>
```

Check:

- task state `SUCCESS`;
- output readable;
- review_status visible;
- governance header/disclaimer in file content if applicable.

Release transition (only for approved outputs):

```bash
curl -X POST http://localhost:8000/outputs/<output_id>/release \
  -H 'Content-Type: application/json' \
  -d '{"author":"pilot_operator"}'
```

Rules:

- `pending_review` and `rejected` outputs cannot be released.
- legacy `accepted` is treated as `approved` for release compatibility.
- successful release returns `review_status=released` and `released_at`.

## 7. KB compile/lint

```bash
curl -X POST http://localhost:8000/kb/compile
curl -X POST http://localhost:8000/kb/lint
curl http://localhost:8000/kb/indexes/master
curl http://localhost:8000/kb/artifacts
curl http://localhost:8000/kb/claims
curl http://localhost:8000/kb/conflicts
```

Check:

- KB task completes;
- master index exists;
- artifacts have source/provenance or lint warnings;
- conflicts are visible.

KB lint severity policy:

- `blocker`: do not proceed with pilot release decision.
- `error`: release only with explicit owner waiver in summary.
- `warning`: allowed with documented residual risk.
- `info`: informational only.

## 8. Release-ready check

```bash
bash scripts/release_ready_check.sh
```

Save artifact directory path from script output.

## 9. Go/No-Go decision

Go only if:

- structural smoke pass;
- quality smoke pass;
- API regression pass;
- KB integration pass;
- pilot preflight pass;
- no open blockers.

No-Go if:

- pipeline fails without clear reason;
- outputs generated without review/governance visibility;
- discovery mode/fallback unclear;
- API/UI not reachable;
- source artifacts not traceable;
- pilot deployment security not documented.

## 10. Stop runtime

```bash
docker compose down
```

Do not remove volumes unless intentionally resetting pilot data.

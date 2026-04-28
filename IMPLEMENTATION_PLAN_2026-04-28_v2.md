# Implementation Plan — 2026-04-28 v2

## 1. Executive Summary

This plan tracks the second autonomous implementation session targeting the CR Intelligence Platform.
Work was executed against `main` branch, base commit `f12dafd` (start of session).

**Session context:**
- Start time: 2026-04-28 11:34:39 MSK
- 50 implementation cycles across 2 sessions

## 2. Cycle Status

### Session 1 (cycles 1–33) — evidence density diagnostics, scoring, evidence report, operator UI panel

| Cycle | Deliverable | Status |
|---|---|---|
| 1–3 | `app/schemas/diagnostics.py` — Pydantic diagnostic schemas | ✅ Complete |
| 4–5 | `app/services/evidence_diagnostics.py` + 2 API endpoints in `documents.py` | ✅ Complete |
| 6–8 | `tests/test_evidence_diagnostics.py` (12 tests) | ✅ Complete |
| 9–11 | `app/services/evidence_report.py` | ✅ Complete |
| 12–14 | `tests/test_evidence_report.py` (17 tests) | ✅ Complete |
| 15–17 | `app/services/scoring/engine.py` — content_kind multipliers + `score_version()` | ✅ Complete |
| 18–19 | `tests/test_scoring.py::TestScoringEngineContentKind` (27 tests) | ✅ Complete |
| 20–22 | `app/api/pipeline.py` + `app/api/outputs.py` — evidence-density + release-evidence | ✅ Complete |
| 23–25 | `app/api/pipeline_stages.py` — corpus-stats endpoint | ✅ Complete |
| 26–28 | `tests/test_pipeline_stages.py` (3 tests) | ✅ Complete |
| 29–31 | `app/ui/components/evidence_state_panel.py` | ✅ Complete |
| 32–33 | `tests/test_evidence_state_panel.py` (17 tests) | ✅ Complete |

### Session 2 (cycles 34–50) — candidate diagnostics, corpus quality, documentation

| Cycle | Deliverable | Status |
|---|---|---|
| 34–36 | `app/services/candidate_engine.py` — `FragmentSkipReason`, `CandidateDiagnosticResult`, `generate_pairs_with_diagnostics()` | ✅ Complete |
| 37–39 | `app/workers/tasks/extract.py` — use diagnostic variant, add `score_version()` call | ✅ Complete |
| 40–42 | `app/services/corpus_quality.py` + `/outputs/corpus-quality` endpoints | ✅ Complete |
| 43–45 | `tests/test_candidate_engine_diagnostics.py` (15 tests) + `tests/test_corpus_quality.py` (19 tests) | ✅ Complete |
| 46–48 | `PRD_CR_Intelligence_Platform_v2_6.md` + `TZ_CR_Intelligence_Platform_v2_5.md` | ✅ Complete |
| 49 | `PROJECT_ANALYSIS_2026-04-28_v3.md` + this plan | ✅ Complete |
| 50 | Full validation + commit + push | ⬜ Pending |

## 3. Files Changed / Created

### New files

```
app/schemas/diagnostics.py
app/services/evidence_diagnostics.py
app/services/evidence_report.py
app/services/corpus_quality.py
app/ui/components/evidence_state_panel.py
tests/test_evidence_diagnostics.py
tests/test_evidence_report.py
tests/test_evidence_state_panel.py
tests/test_candidate_engine_diagnostics.py
tests/test_corpus_quality.py
PRD_CR_Intelligence_Platform_v2_6.md
TZ_CR_Intelligence_Platform_v2_5.md
PROJECT_ANALYSIS_2026-04-28_v3.md
IMPLEMENTATION_PLAN_2026-04-28_v2.md
```

### Modified files

```
app/api/documents.py        — 2 new GET endpoints
app/api/pipeline.py         — 1 new GET endpoint
app/api/outputs.py          — 4 new GET endpoints
app/api/pipeline_stages.py  — 1 new GET endpoint
app/services/scoring/engine.py  — CONTENT_KIND_MULTIPLIER, score_version(), _practical_score(), _score_fragment(content_kind)
app/services/candidate_engine.py  — generate_pairs_with_diagnostics(), CandidateDiagnosticResult, FragmentSkipReason
app/workers/tasks/extract.py  — diagnostic pairs variant, score_version(), richer event log detail
tests/test_scoring.py           — TestScoringEngineContentKind (27 tests)
tests/test_pipeline_stages.py   — corpus-stats endpoint test (3 tests)
```

## 4. Quality Gates

```bash
# Compile check
.venv/bin/python -m py_compile \
  app/schemas/diagnostics.py \
  app/services/evidence_diagnostics.py \
  app/services/evidence_report.py \
  app/services/corpus_quality.py \
  app/services/candidate_engine.py \
  app/services/scoring/engine.py \
  app/api/documents.py \
  app/api/outputs.py \
  app/api/pipeline.py \
  app/api/pipeline_stages.py \
  app/workers/tasks/extract.py \
  app/ui/components/evidence_state_panel.py

# Unit tests
.venv/bin/pytest tests/test_evidence_diagnostics.py \
  tests/test_evidence_report.py \
  tests/test_evidence_state_panel.py \
  tests/test_scoring.py \
  tests/test_pipeline_stages.py \
  tests/test_candidate_engine_diagnostics.py \
  tests/test_corpus_quality.py \
  -q

# Full non-integration test run
.venv/bin/pytest tests/ --ignore=tests/integration -q
```

## 5. Next Steps (Post-Session)

1. Run `RUNTIME_PROFILE=docker-compose-only bash scripts/release_ready_check.sh` against live stack.
2. Verify `/outputs/corpus-quality` returns 200 with `overall_health` key.
3. Spot-check `PipelineEventLog.detail_json` for `candidate_skip_rate` field.
4. Consider integrating `show_corpus_evidence_badge()` into main `app/ui/app.py`.
5. Add UI panel for candidate diagnostics (WP-7 candidate for v2.7).

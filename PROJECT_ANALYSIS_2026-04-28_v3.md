# Project Analysis — 2026-04-28 v3

## 1. Current Stage

```text
Evidence-rich internal pilot operations in progress (v2.6).
```

The previous stage ("Validated JSON-first internal pilot build") has been superseded. All v2.5 deliverables are merged on current head. The v2.6 tranche (candidate diagnostics, corpus quality, content-kind-aware scoring) is also complete on current head.

## 2. What Was Delivered Since Last Analysis (v2 — 2026-04-28)

### 2.1 Evidence Density Diagnostics (cycles 1–14)

| File | Lines | Purpose |
|---|---:|---|
| `app/schemas/diagnostics.py` | ~80 | Pydantic schemas for evidence diagnostic API responses |
| `app/services/evidence_diagnostics.py` | ~320 | `EvidenceDiagnosticsService` — per-version/corpus evidence state |
| `app/services/evidence_report.py` | ~310 | `ReleaseEvidenceReportService` — structured release evidence docs |
| `tests/test_evidence_diagnostics.py` | ~240 | 12 tests |
| `tests/test_evidence_report.py` | ~170 | 17 tests |

### 2.2 Scoring Engine Improvements (cycles 15–19)

| Change | Detail |
|---|---|
| `CONTENT_KIND_MULTIPLIER` constant | `{text:1.0, html:1.0, table_like:0.9, unknown:0.8, image:0.0}` |
| `_score_fragment(content_kind)` | Applies `ck_multiplier`; image → 0.0 |
| `score_version(version_id, model_version_id)` | Per-version incremental scoring |
| `_practical_score(content_kind)` | Returns reduced practical scores for non-text content kinds |
| `tests/test_scoring.py::TestScoringEngineContentKind` | 27 tests |

### 2.3 New API Endpoints (cycles 20–28)

| Endpoint | Module | Response |
|---|---|---|
| `GET /documents/{id}/versions/{vid}/evidence-state` | `app/api/documents.py` | `VersionEvidenceStateOut` |
| `GET /documents/corpus/evidence-coverage` | `app/api/documents.py` | `CorpusCoverageOut` |
| `GET /pipeline/evidence-density` | `app/api/pipeline.py` | `EvidenceStateCountersOut` |
| `GET /outputs/release-evidence` | `app/api/outputs.py` | JSON dict |
| `GET /outputs/release-evidence/markdown` | `app/api/outputs.py` | Markdown text |
| `GET /pipeline/corpus-stats` | `app/api/pipeline_stages.py` | Live corpus metrics |
| `GET /outputs/corpus-quality` | `app/api/outputs.py` | `CorpusQualityReport` JSON |
| `GET /outputs/corpus-quality/markdown` | `app/api/outputs.py` | Markdown text |

### 2.4 Evidence State Operator UI Panel (cycles 29–33)

| File | Lines | Purpose |
|---|---:|---|
| `app/ui/components/evidence_state_panel.py` | ~240 | Streamlit panel with `_STATE_META`, `show_evidence_state_panel()`, `show_corpus_evidence_badge()`, `render_evidence_state_table()` |
| `tests/test_evidence_state_panel.py` | ~220 | 17 tests |

### 2.5 Candidate Generation Diagnostics (cycles 34–39)

| File | Lines | Purpose |
|---|---:|---|
| `app/services/candidate_engine.py` | +~200 | `FragmentSkipReason`, `FragmentCandidateDiagnostic`, `CandidateDiagnosticResult`, `generate_pairs_with_diagnostics()` |
| `app/workers/tasks/extract.py` | +~25 | Uses `generate_pairs_with_diagnostics()`, logs `candidate_skip_rate` etc. into event log; calls `score_version()` |
| `tests/test_candidate_engine_diagnostics.py` | ~290 | 15 tests |

### 2.6 Corpus Quality Monitoring (cycles 40–45)

| File | Lines | Purpose |
|---|---:|---|
| `app/services/corpus_quality.py` | ~280 | `CorpusQualityService`, `CorpusQualityReport`, `ContentKindBreakdown`, `EvidenceRichnessReport`, `CorpusQualityFlag` |
| `tests/test_corpus_quality.py` | ~200 | 19 tests |

### 2.7 Documentation (cycles 46–49)

| File | Purpose |
|---|---|
| `PRD_CR_Intelligence_Platform_v2_6.md` | FR-8 (candidate diagnostics), FR-9 (corpus quality), FR-10 (content-kind scoring) |
| `TZ_CR_Intelligence_Platform_v2_5.md` | WP-1–WP-6 with acceptance criteria; updated validation pack |
| `PROJECT_ANALYSIS_2026-04-28_v3.md` | This document |
| `IMPLEMENTATION_PLAN_2026-04-28_v2.md` | Updated plan marking all cycles complete |

## 3. Test Coverage Summary

| Test File | Tests | Status |
|---|---:|---|
| `test_evidence_diagnostics.py` | 12 | ✅ All pass |
| `test_evidence_report.py` | 17 | ✅ All pass |
| `test_evidence_state_panel.py` | 17 | ✅ All pass |
| `test_scoring.py` (all classes) | 27 | ✅ All pass |
| `test_pipeline_stages.py` | 3 | ✅ All pass |
| `test_candidate_engine_diagnostics.py` | 15 | ✅ All pass |
| `test_corpus_quality.py` | 19 | ✅ All pass |

Total new/extended unit tests: **110**

## 4. API Surface Delta Since v2.5

All endpoints are additive. No existing endpoint signatures were changed.

New endpoints added in this session:

```
GET /documents/{id}/versions/{vid}/evidence-state
GET /documents/corpus/evidence-coverage
GET /pipeline/evidence-density
GET /pipeline/corpus-stats
GET /outputs/release-evidence
GET /outputs/release-evidence/markdown
GET /outputs/corpus-quality
GET /outputs/corpus-quality/markdown
```

## 5. Pipeline Task Delta

`app/workers/tasks/extract.py` `extract_document` now:

1. Uses `generate_pairs_with_diagnostics()` instead of `generate_pairs()`.
2. Logs `candidate_skip_rate`, `fragments_no_mnn`, `fragments_single_mnn`, `fragments_image` into `PipelineEventLog.detail_json`.
3. Calls `score_version(version_id, model_version_id)` in addition to `score_all()`.
4. Logs `version_score_contexts_count` in success event.

## 6. Known Gaps / Next Tranche Candidates

| Gap | Suggested action |
|---|---|
| No alerting for quality flags crossing thresholds | Add webhook/email alert integration WP-7 |
| `score_version()` duplicates work from `score_all()` for just-extracted version | Future: skip version from `score_all()` if `score_version()` was just called |
| UI doesn't yet surface corpus quality badge | Integrate `show_corpus_evidence_badge()` into `app/ui/app.py` |
| Candidate diagnostics not yet surfaced in Streamlit | Add `CandidateDiagnosticResult`-based panel |

## 7. Stage Claims

```text
Current stage as of 2026-04-28 v3: Evidence-rich internal pilot operations in progress.

Next stage: Evidence-rich internal pilot operations RELEASED (requires passing release gate).
```

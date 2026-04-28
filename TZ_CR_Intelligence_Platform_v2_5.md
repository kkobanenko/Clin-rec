# TZ v2.5 — Candidate Diagnostics, Corpus Quality, Content-Kind-Aware Scoring

## 1. Goal Of This Tranche

Extend the evidence-rich internal pilot operations build with:

1. candidate generation diagnostics per fragment;
2. corpus quality monitoring endpoint;
3. content-kind-aware scoring with image zeroing;
4. per-version incremental scoring in extract task.

## 2. Baseline Assumption

The following are already validated on current head:

1. JSON raw artifact persistence.
2. JSON-first normalize flow.
3. Derived blocks artifact generation.
4. Traceability propagation into sections and fragments.
5. Evidence density diagnostics API (`/versions/{id}/evidence-state`, `/corpus/evidence-coverage`).
6. Release evidence report (`/outputs/release-evidence`, `/outputs/release-evidence/markdown`).
7. Evidence state operator UI panel (`app/ui/components/evidence_state_panel.py`).
8. Corpus stats endpoint (`/pipeline/corpus-stats`).
9. Current-head release-ready pack.

## 3. Technical Objective

Add three orthogonal capability layers to the existing pipeline:

| Layer | Module | Key Output |
|---|---|---|
| Candidate diagnostics | `app/services/candidate_engine.py` | `CandidateDiagnosticResult` |
| Corpus quality | `app/services/corpus_quality.py` | `CorpusQualityReport` |
| Content-kind scoring | `app/services/scoring/engine.py` | `CONTENT_KIND_MULTIPLIER`, `score_version()` |

All three layers are additive and do not break existing API contracts.

## 4. Work Packages

### WP-1. Candidate Generation Diagnostics *(DELIVERED)*

**Files changed:**
- `app/services/candidate_engine.py` — added `FragmentSkipReason`, `FragmentCandidateDiagnostic`, `CandidateDiagnosticResult`, `generate_pairs_with_diagnostics()`, `_process_fragment_diagnostic()`
- `app/workers/tasks/extract.py` — replaced `generate_pairs()` with `generate_pairs_with_diagnostics()`, logging `skip_rate`, `fragments_no_mnn`, `fragments_single_mnn`, `fragments_image` into `PipelineEventLog.detail_json`

**Acceptance criteria:**
1. `generate_pairs_with_diagnostics` produces same DB side-effects as `generate_pairs`.
2. `CandidateDiagnosticResult.to_dict()` serialises all counters without error.
3. `skip_rate` is in [0,1] for any input.
4. Image fragments have `skip_reason == IMAGE_FRAGMENT` and do not trigger MNN extraction.

**Tests:** `tests/test_candidate_engine_diagnostics.py` (15 tests).

### WP-2. Corpus Quality Monitoring *(DELIVERED)*

**Files changed:**
- `app/services/corpus_quality.py` — new service with `CorpusQualityService`, `CorpusQualityReport`, `ContentKindBreakdown`, `EvidenceRichnessReport`, `CorpusQualityFlag`
- `app/api/outputs.py` — added `/outputs/corpus-quality` (JSON) and `/outputs/corpus-quality/markdown` (Markdown) endpoints

**Acceptance criteria:**
1. `CorpusQualityService.generate_report()` returns `CorpusQualityReport` on empty corpus with `overall_health == "empty"`.
2. Image-heavy corpus (≥40%) produces `image_fraction` flag.
3. Low evidence coverage (<5%) produces `evidence_coverage` flag.
4. Custom thresholds override defaults.
5. `to_markdown()` produces a document with `# Corpus Quality Report` header.

**Tests:** `tests/test_corpus_quality.py` (19 tests).

### WP-3. Content-Kind-Aware Scoring *(DELIVERED)*

**Files changed:**
- `app/services/scoring/engine.py` — added `CONTENT_KIND_MULTIPLIER`, `_practical_score(content_kind)`, updated `_score_fragment(evidence, weights, content_kind)`, added `score_version(version_id, model_version_id)`
- `app/workers/tasks/extract.py` — added `score_version()` call after `score_all()`

**Acceptance criteria:**
1. `_score_fragment(evidence, weights, content_kind="image")` returns 0.0 for any evidence.
2. `_score_fragment(evidence, weights, content_kind="text")` returns a value in (0, 1].
3. `CONTENT_KIND_MULTIPLIER["image"] == 0.0`.
4. `score_version()` queries only fragments under the target `version_id`.

**Tests:** `tests/test_scoring.py::TestScoringEngineContentKind` (27 tests).

### WP-4. Evidence Diagnostics Service *(DELIVERED — from TZ v2.4)*

See `app/services/evidence_diagnostics.py` and `tests/test_evidence_diagnostics.py` (12 tests).

### WP-5. Evidence State Operator UI Panel *(DELIVERED — from TZ v2.4)*

See `app/ui/components/evidence_state_panel.py` and `tests/test_evidence_state_panel.py` (17 tests).

### WP-6. Release Evidence Report *(DELIVERED — from TZ v2.4)*

See `app/services/evidence_report.py` and `tests/test_evidence_report.py` (17 tests).

## 5. Technical Constraints

1. No breaking changes in `/documents`, `/matrix`, `/pipeline`, `/outputs`.
2. No replacement of JSON by HTML/PDF as primary source.
3. No external raw artifact fetch during current version preview/download/review.
4. Runtime validation is mandatory; unit tests alone are not sufficient.
5. Image fragments must contribute 0.0 to any evidence score.
6. Candidate diagnostics must not call `load_dictionary()` for image fragments.

## 6. Required Validation Pack

```bash
python -m py_compile \
  app/services/candidate_engine.py \
  app/services/corpus_quality.py \
  app/services/evidence_diagnostics.py \
  app/services/evidence_report.py \
  app/services/scoring/engine.py \
  app/api/documents.py \
  app/api/outputs.py \
  app/api/pipeline.py \
  app/api/pipeline_stages.py \
  app/workers/tasks/extract.py \
  app/ui/components/evidence_state_panel.py

python -m pytest -q \
  tests/test_candidate_engine_diagnostics.py \
  tests/test_corpus_quality.py \
  tests/test_evidence_diagnostics.py \
  tests/test_evidence_report.py \
  tests/test_evidence_state_panel.py \
  tests/test_scoring.py \
  tests/test_pipeline_stages.py

bash scripts/pilot_preflight.sh
RUNTIME_PROFILE=docker-compose-only bash scripts/release_ready_check.sh
```

## 7. Acceptance

This tranche is accepted if:

1. Current-head release-ready pack passes.
2. All unit tests listed above pass.
3. `/outputs/corpus-quality` returns valid JSON with `overall_health` key.
4. `PipelineEventLog.detail_json` for a completed extract task includes `candidate_skip_rate`.
5. No image fragment produces a positive `final_fragment_score`.
6. JSON-derived sections and fragments remain > 0 on current-head runtime.

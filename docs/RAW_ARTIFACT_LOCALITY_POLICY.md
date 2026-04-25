# RAW_ARTIFACT_LOCALITY_POLICY

## Principle

Raw artifact UI actions are **local-storage-only** actions.
They must not fetch from the source web service.

## Bindings

| Action | Allowed data source | Forbidden data source |
|---|---|---|
| Download button | Local MinIO/S3 via `app.core.storage.download_artifact` | `doc.html_url`, `doc.pdf_url`, any external URL |
| Preview | Bytes from Download path above | External iframe, `http://app:8000` browser-side, external URL |
| Load Evidence | `GET /matrix/pair-evidence?document_version_id=…` | External sources |
| Artifact Coverage | `GET /documents/artifact-coverage` | External sources |

## Implementation

- `app/ui/app.py` — `fetch_artifact_bytes()` calls `http://app:8000` **server-side** from the Streamlit container. The result bytes are passed to `st.download_button`. The browser never sees `http://app:8000`.
- `app/api/documents.py` — `download_document_artifact` reads from `download_artifact(artifact.raw_path)` which calls MinIO.
- `app/api/documents.py` — `get_artifact_coverage` validates each artifact from local storage only. No HTTP calls to external services.

## Coverage Diagnostic

`GET /documents/artifact-coverage` returns aggregate health of local artifact storage.
A release must not ship if `artifacts_downloadable == 0` for all documents with `current_versions_with_artifacts == 0`.

## Backfill

When local artifacts are missing:

```bash
python scripts/backfill_missing_raw_artifacts.py --dry-run   # see what would run
python scripts/backfill_missing_raw_artifacts.py              # queue fetch tasks
```

Fetch tasks are queued via Celery and store artifacts in MinIO.
The backfill does not DELETE existing artifacts.

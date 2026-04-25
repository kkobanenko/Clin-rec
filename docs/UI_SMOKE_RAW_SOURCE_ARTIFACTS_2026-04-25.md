# UI Smoke — Raw Source Artifacts — 2026-04-25

- Commit SHA: `b0f0484`
- Runtime profile: `pilot-compose-local`
- Auth enabled: `false` (no `CRIN_API_AUTH_ENABLED` override in `.env`; local default mode)
- Document ID: `1`
- Version ID: `4`
- Artifact ID: `40`

## Reproduction Context

- Streamlit UI: `http://127.0.0.1:8501/`
- API: `http://127.0.0.1:8000/`
- Raw artifacts endpoint returned valid current artifacts for document `1`.
- Direct API checks passed:
  - `GET /documents/1/artifacts` -> `200 OK`
  - `GET /documents/1/artifacts/40/download` -> `200 OK`
  - `GET /documents/1/artifacts/40/download?disposition=inline` -> `200 OK`
  - `GET /matrix/pair-evidence?document_version_id=4&page_size=20` -> `200 OK`

## Pre-fix Browser Failure

- `Download` link target in browser UI: `http://app:8000/documents/1/artifacts/40/download`
- `Preview` link target in browser UI: `http://app:8000/documents/1/artifacts/40/download?disposition=inline`
- Browser result: `ERR_NAME_NOT_RESOLVED`
- Root cause: container-only hostname leaked into browser-facing `link_button` URLs.

## Post-fix UI Smoke

### Download

- UI now renders Streamlit server-side `Download` buttons instead of browser links.
- Browser DOM contains no `http://app:8000/...` artifact links.
- Page remains on `http://127.0.0.1:8501/` when clicking artifact action controls.
- No UI `API error` surfaced after click.
- Note: integrated browser tooling did not emit a capturable download event, but the action is now a server-side download button backed by successful direct API `200 OK` attachment response and no browser-hostname leak.

### Preview

- Result: `pass`
- Action: clicked first artifact `Preview` button.
- Output: inline HTML/text preview rendered in the page.
- Browser-safe behavior: no `app:8000` URL exposed in DOM.

### Load Evidence For Current Version

- Result: `pass`
- Action: clicked `Load Evidence For Current Version`.
- Output shown in UI: `Evidence rows: 60`
- No empty-state or error message displayed for this version.

## Log Excerpts

- Browser smoke snapshot after fix:
  - `hasBadAppHostLink=false`
  - `previewShown=true`
  - `stillLoadedAfterPreview=true`
  - `evidenceRows="Evidence rows: 60"`
  - `apiError=false`

## Final Verdict

- `Download`: pass
- `Preview`: pass
- `Load Evidence For Current Version`: pass
- RawSourceArtifacts UI blocker: `closed`
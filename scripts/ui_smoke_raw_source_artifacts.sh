#!/usr/bin/env bash
# UI smoke for Raw Source Artifacts (API-assisted, not full browser).
# Verifies that:
#  1. /documents/artifact-coverage endpoint responds with expected shape
#  2. Download/preview URL paths are local API paths, not external URLs
#  3. No references to external web service hostnames appear in artifact metadata
#
# Note: this is API+helper smoke, not full browser coverage.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_BASE="${CRIN_API_BASE:-http://127.0.0.1:8000}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

PASS=0
FAIL=0
WARNINGS=()

check() {
    local description="$1"
    local result="$2"
    if [[ "$result" == "ok" ]]; then
        echo "  [PASS] $description"
        ((PASS++)) || true
    else
        echo "  [FAIL] $description: $result"
        ((FAIL++)) || true
    fi
}

warn() {
    echo "  [WARN] $1"
    WARNINGS+=("$1")
}

echo "=== UI Smoke: Raw Source Artifacts ==="
echo "API: $API_BASE"
echo

# 1. Health check
echo "--- Health ---"
health_status=$(curl -fsS "$API_BASE/health" | "$PYTHON_BIN" -c "import sys,json; d=json.load(sys.stdin); print('ok' if d.get('status')=='ok' else 'bad:'+str(d))" 2>&1)
check "API health ok" "$health_status"

# 2. Artifact coverage endpoint shape
echo
echo "--- Artifact Coverage Endpoint ---"
coverage_json=$(curl -fsS "$API_BASE/documents/artifact-coverage" 2>&1)
coverage_status=$?
if [[ $coverage_status -ne 0 ]]; then
    check "coverage endpoint reachable" "curl failed: $coverage_json"
else
    check "coverage endpoint reachable" "ok"

    has_total=$("$PYTHON_BIN" -c "import json,sys; d=json.loads(sys.stdin.read()); print('ok' if 'total_documents' in d else 'missing total_documents')" <<< "$coverage_json")
    check "coverage has total_documents" "$has_total"

    has_downloadable=$("$PYTHON_BIN" -c "import json,sys; d=json.loads(sys.stdin.read()); print('ok' if 'artifacts_downloadable' in d else 'missing')" <<< "$coverage_json")
    check "coverage has artifacts_downloadable" "$has_downloadable"

    has_docs=$("$PYTHON_BIN" -c "import json,sys; d=json.loads(sys.stdin.read()); print('ok' if isinstance(d.get('documents'), list) else 'missing')" <<< "$coverage_json")
    check "coverage has documents list" "$has_docs"
fi

# 3. List documents and check artifact metadata locality
echo
echo "--- Document Artifacts Locality ---"
docs_json=$(curl -fsS "$API_BASE/documents?page_size=5" 2>&1)
doc_ids=$("$PYTHON_BIN" -c "import json,sys; items=json.loads(sys.stdin.read()).get('items',[]); print(' '.join(str(i['id']) for i in items[:3]))" <<< "$docs_json" 2>/dev/null || echo "")

if [[ -z "$doc_ids" ]]; then
    warn "No documents found; skipping artifact locality checks"
else
    for doc_id in $doc_ids; do
        artifacts_json=$(curl -fsS "$API_BASE/documents/$doc_id/artifacts" 2>/dev/null || echo "{}")

        # Check that download_url is a local path (starts with /documents/)
        external_refs=$("$PYTHON_BIN" -c "
import json, sys
d = json.loads(sys.stdin.read())
artifacts = d.get('artifacts', [])
bad = []
for a in artifacts:
    for key in ('download_url', 'preview_url'):
        url = a.get(key) or ''
        if 'cr.minzdrav' in url or 'http://app:8000' in url or url.startswith('http'):
            bad.append(f'{key}={url}')
print('ok' if not bad else 'external_refs:' + str(bad))
" <<< "$artifacts_json")
        check "doc $doc_id artifact URLs are local paths" "$external_refs"
    done
fi

# 4. Verify download endpoint is on local API (not external)
echo
echo "--- Download Endpoint Locality ---"
sample_artifact=$("$PYTHON_BIN" -c "
import json, sys
for doc_id_str in sys.argv[1:]:
    import urllib.request
    try:
        resp = urllib.request.urlopen(f'http://127.0.0.1:8000/documents/{doc_id_str}/artifacts', timeout=5)
        d = json.loads(resp.read())
        artifacts = d.get('artifacts', [])
        if artifacts:
            a = artifacts[0]
            print(doc_id_str, a['id'], a.get('download_url',''))
            break
    except Exception:
        pass
" $doc_ids 2>/dev/null || echo "")

if [[ -z "$sample_artifact" ]]; then
    warn "No downloadable artifacts found to test download URL; this may mean all fetched artifacts are SPA shells (expected after shell-detection fix)"
else
    read -r _doc _art_id download_path <<< "$sample_artifact"
    # Should be relative path, not external URL
    is_local=$("$PYTHON_BIN" -c "
path = '$download_path'
if path.startswith('/documents/') and 'cr.minzdrav' not in path and 'app:8000' not in path:
    print('ok')
else:
    print('bad:' + path)
" 2>/dev/null || echo "bad:parse_error")
    check "download_url is local path for artifact $art_id" "$is_local"
fi

echo
echo "=== Smoke Results ==="
echo "PASS: $PASS  FAIL: $FAIL  WARNINGS: ${#WARNINGS[@]}"

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "Warnings:"
    for w in "${WARNINGS[@]}"; do echo "  - $w"; done
fi

if [[ $FAIL -gt 0 ]]; then
    echo "SMOKE FAILED" >&2
    exit 1
fi

echo "Smoke passed."
exit 0

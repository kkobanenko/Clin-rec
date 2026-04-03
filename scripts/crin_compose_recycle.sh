#!/usr/bin/env bash
# Безопасное освобождение портов проекта crin (в т.ч. 8000 для crin_app).
# Только docker compose в каталоге репозитория — см. ISOLATION_POLICY.md
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "Clin-rec: docker compose down (project crin)..."
docker compose down
echo "Clin-rec: docker compose up -d ..."
docker compose up -d
echo "Clin-rec: status"
docker compose ps

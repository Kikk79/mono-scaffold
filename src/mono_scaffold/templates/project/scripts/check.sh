#!/usr/bin/env bash
# Qualitäts-Gate vor jedem Merge: ruff, Modulgrenzen (import-linter), Tests.
# Alle Schritte laufen auch nach einem Fehler weiter, damit ein Lauf das Gesamtbild zeigt;
# der Exit-Code ist ungleich 0, sobald ein Schritt scheitert.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$(dirname "$0")/.."

failed=()
run_step() {
    local label="$1"; shift
    echo "==> $label: $*"
    if "$@"; then echo "==> $label: OK"; else echo "==> $label: FEHLGESCHLAGEN"; failed+=("$label"); fi
    echo
}

run_step ruff uv run ruff check app tests scripts alembic
run_step lint-imports uv run lint-imports --no-cache
run_step pytest uv run pytest -q
if [[ -d frontend ]]; then
    run_step frontend-test bash -c 'cd frontend && bun test'
fi

if ((${#failed[@]} > 0)); then
    echo "check.sh: fehlgeschlagen: ${failed[*]}"
    exit 1
fi
echo "check.sh: alle Prüfungen grün"

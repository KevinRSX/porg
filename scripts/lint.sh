#!/usr/bin/env bash
set -euo pipefail

# Usage: ./lint.sh [check|fix] [paths...]
#   check (default): verify formatting & lint; no changes written
#   fix            : apply formatting & auto-fixes in place
#
# Examples:
#   ./lint.sh
#   ./lint.sh fix
#   ./lint.sh check src tests

MODE="${1:-check}"
# If first arg is a mode, shift it off; otherwise treat all args as paths.
if [[ "$MODE" == "check" || "$MODE" == "fix" ]]; then
  shift || true
else
  MODE="check"
fi

# Default to the python directory if no paths are provided.
PATHS=("$@")
if [[ ${#PATHS[@]} -eq 0 ]]; then
  PATHS=("python")
fi

if [[ "$MODE" == "fix" ]]; then
  echo "ruff format (write changes)…"
  ruff format "${PATHS[@]}"
  echo "ruff check (apply fixes)…"
  ruff check --fix "${PATHS[@]}"
else
  echo "ruff format (check only)…"
  ruff format --check "${PATHS[@]}"
  echo "ruff check…"
  ruff check "${PATHS[@]}"
fi

echo "Lint passed."